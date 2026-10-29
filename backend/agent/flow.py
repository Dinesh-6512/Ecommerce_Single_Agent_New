"""
LangGraph flow for 'Ask the Store' with Langfuse Tracing.

Flow sequence:
1. User question
2. check_question: Validates if the question is related to the store
   (products, prices, stock, or the user's shopping cart).
3. Route:
   - If UNRELATED -> refuse_unrelated -> final answer
   - If STORE -> fetch_store_data -> generate_answer -> final answer
4. Data access is strictly read-only and bound to the logged-in user's ID.
5. All executions are traced in Langfuse (flow, Groq model call, database step, timing).
"""
import os
from typing import TypedDict, Any, Dict, Optional, List
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

try:
    from .llm import get_groq_model
    from .data_access import get_agent_products, search_agent_products, get_agent_user_cart
    from .tracing import create_agent_trace
    from ..database import SessionLocal
except ImportError:
    from agent.llm import get_groq_model
    from agent.data_access import get_agent_products, search_agent_products, get_agent_user_cart
    from agent.tracing import create_agent_trace
    from database import SessionLocal


class AgentState(TypedDict, total=False):
    question: str
    user_id: int
    db: Any
    trace: Any
    is_store_query: bool
    retrieved_data: Dict[str, Any]
    answer: str


CLASSIFICATION_PROMPT = """You are a strict intent classifier for an e-commerce store assistant.
Determine whether the user question is related to our store.

A valid store question MUST be about one of these topics:
1. Store products, item descriptions, specifications, or categories.
2. Product prices, costs, or discounts.
3. Product inventory, availability, or stock levels.
4. The user's shopping cart (items currently in cart, quantities, cart total).

User Question: "{question}"

If the question is about store products, prices, stock, or the user's shopping cart, reply with: STORE
If the question is about anything else (e.g., general knowledge, math, coding, chit-chat, other unrelated topics), reply with: UNRELATED

Respond with only one word: STORE or UNRELATED."""


SYSTEM_ANSWER_PROMPT = """You are the "Ask the Store" assistant for an online shop.
Answer the user's question using ONLY the real database data provided below.

CRITICAL RULES:
1. Use real database data only. NEVER invent, assume, or hallucinate products, prices, stock numbers, or cart items.
2. If no product or cart data matches the question, clearly state that no matching information was found in the store.
3. For questions regarding the cart, use ONLY the Cart Data belonging to the logged-in user provided below.
4. You are strictly a read-only assistant. If the user asks to buy, add to cart, remove items, or update stock, politely explain that you cannot perform changes and they can use the store buttons directly.
5. Provide a helpful, clear, and concise answer.

STORE DATABASE DATA:
--- PRODUCT CATALOG ---
{products_catalog}

--- LOGGED-IN USER CART (User ID: {user_id}) ---
{cart_summary}

USER QUESTION:
{question}
"""


def check_question_node(state: AgentState) -> Dict[str, Any]:
    """
    Checks if the user's question is a store question (products, prices, stock, user cart).
    Traced in Langfuse under 'check_question_intent'.
    """
    question = state.get("question", "").strip()
    trace = state.get("trace")
    span = trace.span(name="check_question_intent", input={"question": question}) if trace else None

    if not question:
        if span:
            span.end(output={"is_store_query": False, "reason": "empty_question"})
        return {"is_store_query": False}

    try:
        llm = get_groq_model(temperature=0.0)
        prompt = CLASSIFICATION_PROMPT.format(question=question)
        response = llm.invoke(prompt)
        verdict = response.content.strip().upper()

        is_store = "STORE" in verdict
        if span:
            span.end(output={"verdict": verdict, "is_store_query": is_store})
        return {"is_store_query": is_store}
    except Exception as e:
        if span:
            span.end(level="ERROR", status_message=str(e)[:200])
        raise e


def route_question(state: AgentState) -> str:
    """
    Conditional router: routes to data fetching if store query, else to polite refusal.
    """
    if state.get("is_store_query", False):
        return "fetch_store_data"
    return "refuse_unrelated"


def refuse_unrelated_node(state: AgentState) -> Dict[str, Any]:
    """
    Politely refuses questions that are not related to the store.
    Marks trace as 'refused' and 'out-of-scope'.
    """
    refusal_message = (
        "I am an assistant for this store and can only help with questions about "
        "our products, prices, stock availability, and your shopping cart. "
        "Please feel free to ask anything about our store items or your cart!"
    )
    trace = state.get("trace")
    if trace:
        span = trace.span(name="refuse_unrelated", input={"question": state.get("question", "")})
        span.end(output={"answer": refusal_message, "status": "refused"})
        trace.update(
            tags=["store-agent", "refused", "out-of-scope"],
            metadata={"status": "refused", "category": "out-of-scope"}
        )

    return {"answer": refusal_message}


def fetch_store_data_node(state: AgentState) -> Dict[str, Any]:
    """
    Reads approved real database data (read-only) for products, stock, prices, and user cart.
    Ensures cart data is scoped strictly to the logged-in user's ID.
    Traced in Langfuse under 'database_read_step'.
    """
    user_id = state.get("user_id", 0)
    question = state.get("question", "")
    trace = state.get("trace")
    span = trace.span(name="database_read_step", input={"user_id": user_id, "query": question}) if trace else None

    db: Optional[Session] = state.get("db")
    close_db_after = False

    if db is None:
        db = SessionLocal()
        close_db_after = True

    try:
        # 1. Read catalog products (read-only)
        all_products = get_agent_products(db, limit=50)

        # Also run keyword search to highlight specific matches
        matched_products = search_agent_products(db, query=question, limit=10) if question else []

        # 2. Read user cart (read-only, strictly for this user_id)
        user_cart = get_agent_user_cart(db, user_id=user_id)

        has_catalog = len(all_products) > 0
        has_matched = len(matched_products) > 0

        # Check if question targeted an unavailable product
        is_no_data = False
        if not has_matched and any(
            w in question.lower()
            for w in ["shoes", "boots", "jacket", "shirt", "pants", "camera", "tv", "phone", "coffee"]
        ):
            is_no_data = True

        if span:
            span.end(output={
                "catalog_products_count": len(all_products),
                "matched_products_count": len(matched_products),
                "cart_items_count": len(user_cart.get("items", [])),
                "has_data": has_catalog,
            })
            if is_no_data or not has_catalog:
                trace.update(
                    tags=["store-agent", "no-data"],
                    metadata={"status": "no-data"}
                )

        retrieved = {
            "products": all_products,
            "matched_products": matched_products,
            "user_cart": user_cart,
            "has_products": has_catalog,
        }
        return {"retrieved_data": retrieved}
    except Exception as e:
        if span:
            span.end(level="ERROR", status_message=str(e)[:200])
        raise e
    finally:
        if close_db_after and db is not None:
            db.close()


def generate_answer_node(state: AgentState) -> Dict[str, Any]:
    """
    Uses the Groq model to write the final answer using real database data only.
    Traced in Langfuse under 'groq_model_call'.
    """
    question = state.get("question", "")
    user_id = state.get("user_id", 0)
    retrieved = state.get("retrieved_data", {})
    trace = state.get("trace")

    products = retrieved.get("products", [])
    user_cart = retrieved.get("user_cart", {})

    # Format product catalog
    if not products:
        products_text = "No products found in the store database."
    else:
        product_lines = []
        for p in products:
            product_lines.append(
                f"- Product #{p['id']}: {p['title']} | Price: ${p['price']:.2f} | "
                f"Stock: {p['stock']} units available | Description: {p['description']}"
            )
        products_text = "\n".join(product_lines)

    # Format cart summary for the logged-in user
    cart_items = user_cart.get("items", [])
    cart_total = user_cart.get("total", 0.0)

    if not cart_items:
        cart_text = f"Your shopping cart is currently empty (0 items, Total: $0.00)."
    else:
        cart_lines = [f"Cart Total: ${cart_total:.2f}"]
        for item in cart_items:
            cart_lines.append(
                f"- {item['product_title']} (ID: {item['product_id']}) x {item['quantity']} "
                f"@ ${item['price']:.2f} each = Subtotal: ${item['subtotal']:.2f} "
                f"(Current Store Stock: {item['available_stock']})"
            )
        cart_text = "\n".join(cart_lines)

    llm = get_groq_model(temperature=0.0)
    prompt = SYSTEM_ANSWER_PROMPT.format(
        products_catalog=products_text,
        user_id=user_id,
        cart_summary=cart_text,
        question=question
    )

    groq_gen = trace.generation(
        name="groq_model_call",
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        input={"prompt_length": len(prompt), "question": question},
        model_parameters={"temperature": 0.0}
    ) if trace else None

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()

        if groq_gen:
            groq_gen.end(output={"answer": answer})

        # Check if LLM response indicates no-data
        lower_ans = answer.lower()
        if any(term in lower_ans for term in ["do not carry", "no matching product", "not found in the store", "empty"]):
            if trace:
                trace.update(
                    tags=["store-agent", "no-data"],
                    metadata={"status": "no-data"}
                )

        return {"answer": answer}
    except Exception as e:
        if groq_gen:
            groq_gen.end(level="ERROR", status_message=str(e)[:200])
        raise e


def build_store_agent_graph():
    """
    Constructs and compiles the LangGraph StateGraph workflow for Ask the Store.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("check_question", check_question_node)
    workflow.add_node("refuse_unrelated", refuse_unrelated_node)
    workflow.add_node("fetch_store_data", fetch_store_data_node)
    workflow.add_node("generate_answer", generate_answer_node)

    workflow.set_entry_point("check_question")

    workflow.add_conditional_edges(
        "check_question",
        route_question,
        {
            "fetch_store_data": "fetch_store_data",
            "refuse_unrelated": "refuse_unrelated",
        }
    )

    workflow.add_edge("refuse_unrelated", END)
    workflow.add_edge("fetch_store_data", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow.compile()


store_agent_graph = build_store_agent_graph()


def run_store_agent(question: str, user_id: int, db: Optional[Session] = None) -> str:
    """
    Convenience function to execute the LangGraph Ask the Store flow with Langfuse tracing.
    Returns the final answer string.
    """
    trace, client = create_agent_trace(user_id=user_id, question=question)

    initial_state: AgentState = {
        "question": question,
        "user_id": user_id,
        "db": db,
        "trace": trace,
    }

    try:
        result = store_agent_graph.invoke(initial_state)
        answer = result.get("answer", "")
        if trace:
            trace.update(output={"answer": answer})
        if client:
            client.flush()
        return answer
    except Exception as e:
        if trace:
            trace.update(
                output={"error": "Agent execution failed"},
                level="ERROR",
                status_message=str(e)[:200]
            )
        if client:
            client.flush()
        raise e
