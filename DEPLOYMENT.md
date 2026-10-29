# Deployment Guide: Local & Render Cloud

This document provides complete, step-by-step instructions for deploying our full-stack e-commerce application locally and to the **Render** cloud platform.

---

## 1. Cloud Architecture & Deployment Order

The cloud deployment consists of **three parts**, deployed in this exact sequence:

```mermaid
graph TD
    subgraph Step 1: Database
    A[(Neon PostgreSQL Cloud DB)]
    end

    subgraph Step 2: Backend
    B[Render Web Service: FastAPI] -->|DATABASE_URL via SSL| A
    end

    subgraph Step 3: Frontend
    C[Render Static Site: ReactJS] -->|VITE_API_URL| B
    end

    Browser([Customer Browser]) -->|HTTPS| C
```

1. **Step 1: PostgreSQL Database on Neon** (Already cloud-hosted; zero server maintenance).
2. **Step 2: FastAPI Backend on Render** (Deploys as a Python **Web Service**).
3. **Step 3: ReactJS Frontend on Render** (Deploys as a fast, global **Static Site**).

---

## 2. GitHub Integration & Security Verification

Before deploying to Render, the project is pushed to GitHub. Render automatically detects commits and builds the latest version.

### 1. Main `.gitignore` Protection
The project includes a root [.gitignore](file:///c:/Users/dines/Documents/Ecommerce_new/.gitignore) ensuring secrets and local artifacts are never committed:
* `.env`, `backend/.env`, `frontend/.env`, `*.env` (Hides all passwords and secret keys)
* `venv/`, `.venv/` (Hides local Python virtual environments)
* `__pycache__/`, `*.pyc` (Hides Python bytecode cache)
* `node_modules/` (Hides downloaded npm packages)
* `dist/` (Hides compiled production builds)

### 2. Pushing the Project to GitHub
1. Go to [github.com](https://github.com) and click **"New repository"**.
2. Name it (for example: `ecommerce-app`), select **Public** or **Private**, and click **"Create repository"** (do NOT initialize with README).
3. In your local terminal, link and push your code:
   ```powershell
   git remote add origin https://github.com/<your-username>/ecommerce-app.git
   git branch -M main
   git push -u origin main
   ```

### 3. Verify No Secrets on GitHub
Visit your GitHub repository in your browser:
* Confirm `backend/.env` is **NOT** present in the file tree.
* Confirm `frontend/.env` is **NOT** present in the file tree.
* Confirm no passwords, database links, or secret keys appear in any committed file.

---

## 3. Neon PostgreSQL Database Integration

### 1. Create Neon Project & Database
1. Go to [neon.tech](https://neon.tech) and log in.
2. Click **"Create Project"**:
   * **Project Name**: `ecommerce-db`
   * **Region**: Select the region closest to you (e.g., AWS US East, Singapore, or Frankfurt).
   * Click **"Create"**.

### 2. Copy the Connection String
1. On your Neon project dashboard, click the **Connect** button at the top.
2. Set **Connection pooling** to **ON** (recommended for scalable web apps).
3. Copy the pooled connection string.

### 3. Change Prefix for psycopg (v3) Driver
Neon provides a connection string starting with `postgresql://`. Because our [backend/requirements.txt](file:///c:/Users/dines/Documents/Ecommerce_new/backend/requirements.txt) uses the high-performance modern **`psycopg` (version 3)** driver, update the beginning of the URL:
* **Original Neon Link**:
  ```text
  postgresql://user:password@ep-xyz-pooler.region.aws.neon.tech/neondb?sslmode=require
  ```
* **Required SQLAlchemy Format**:
  ```text
  postgresql+psycopg://user:password@ep-xyz-pooler.region.aws.neon.tech/neondb?sslmode=require
  ```
*(Ensure `?sslmode=require` remains at the end).*

### 4. Local Testing with Neon
Add the connection string to `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://user:password@ep-xyz-pooler.region.aws.neon.tech/neondb?sslmode=require
```
When FastAPI starts, it connects over SSL, creates all 4 tables (`users`, `products`, `cart`, `cart_items`), and seeds sample products. The health check confirms this:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/health
```

---

## 4. Render Deployment Settings

### Part 2: FastAPI Backend (Render Web Service)
In the Render dashboard, click **New +** $\rightarrow$ **Web Service**:

| Setting | Value | Why It Is Used |
| :--- | :--- | :--- |
| **Name** | `ecommerce-backend` | Name of your backend service. |
| **Language** | `Python` | Runtime environment. |
| **Root Directory** | `backend` | Tells Render to run commands inside the `backend/` folder. |
| **Build Command** | `pip install -r requirements.txt` | Installs FastAPI, SQLAlchemy, psycopg, pyjwt, bcrypt. |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` | Starts the production ASGI server on the port assigned by Render. |
| **Instance Type** | `Free` | Free tier web service. |

> [!NOTE]
> Once deployed, Render provides a public HTTPS URL (e.g., `https://ecommerce-backend.onrender.com`).  
> Verify it by visiting `https://ecommerce-backend.onrender.com/api/health`.

---

### Part 3: Render Frontend Deployment (Render Static Site)

Follow these exact steps to deploy the ReactJS frontend on Render and connect it to your live FastAPI backend:

#### RENDER FRONTEND STEPS:
1. In Render, click **New +** at the top right and choose **Static Site**.
2. Select the same GitHub repository (`Dinesh-6512/Ecommerce_new`) and click **Connect**.
3. Fill in the settings:
   * **Name**: `ecommerce-frontend`
   * **Branch**: `main`
   * **Root Directory**: `frontend` (the real frontend folder)
   * **Build Command**: `npm install && npm run build`
   * **Publish Directory**: `dist`
4. Scroll down to **Environment Variables** and click **Add Environment Variable**. Add:
   * **Key**: `VITE_API_URL`
   * **Value**: `<backend-url>/api`  
     *(Example: `https://ecommerce-backend.onrender.com/api` — the value must end with `/api` and must NOT have a trailing `/` after it).*
5. Click **Create Static Site** and wait until the status shows **Live**.
6. Open the Static Site dashboard, go to the **Redirects / Rewrites** tab and click **Add Rule**:
   * **Source**: `/*`
   * **Destination**: `/index.html`
   * **Action**: `Rewrite`
   * Click **Save Changes**. *(This prevents "Not Found" 404 errors whenever a subpage such as `/cart` or `/login` is refreshed).*
7. Copy your live frontend URL (example: `https://ecommerce-frontend.onrender.com`).
8. If `VITE_API_URL` is changed later, redeploy the frontend (**Manual Deploy** $\rightarrow$ **Clear build cache & deploy**), because Vite reads and embeds environment variables only during the build step.

> [!TIP]
> **Troubleshooting Node Version**: If the Render build fails with a Node version error, add the environment variable `NODE_VERSION = 22` under the **Environment** tab and redeploy.

---

## 5. Environment Variables Table

Set these in the **Environment** tab on Render. Only variable names are shown (never real secrets in documentation):

### Backend Environment Variables (Render Web Service)
| Variable Name | Required Value Description |
| :--- | :--- |
| `DATABASE_URL` | Your Neon connection string with `postgresql+psycopg://` and `?sslmode=require`. |
| `SECRET_KEY` | 32-byte secret hex key generated using `secrets.token_hex(32)`. |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) |
| `GROQ_API_KEY` | Your Groq API key from console.groq.com (starts with `gsk_`). |
| `GROQ_MODEL` | The selected free Groq model name: `llama-3.3-70b-versatile`. |
| `LANGFUSE_PUBLIC_KEY` | Your Langfuse project public key (starts with `pk-lf-`). |
| `LANGFUSE_SECRET_KEY` | Your Langfuse project secret key (starts with `sk-lf-`). |
| `LANGFUSE_HOST` | Your Langfuse cloud host URL: `https://cloud.langfuse.com`. |

### Frontend Environment Variables (Render Static Site)
| Variable Name | Required Value Description |
| :--- | :--- |
| `VITE_API_URL` | The live URL of your deployed Render backend ending in `/api` (e.g., `https://ecommerce-backend.onrender.com/api`). |


---

## 6. How the First Admin User is Created

When the backend starts up on Render for the very first time:
1. FastAPI's lifespan startup handler automatically checks the `users` table in Neon.
2. If no admin exists, it automatically creates the default administrator account:
   * **Email**: `admin@store.com`
   * **Password**: `AdminPass123!`
   * **Role**: `is_admin = True`
3. The admin can immediately log in from the frontend at `/login` to access the protected **Add Product** screen and publish items.

---

## 7. Exact Deployment Steps in Order

When ready to deploy online:

1. **Step 1: Push Code to GitHub**
   * Stage and push all project files. Confirm `.env` files are not on GitHub.
2. **Step 2: Neon Cloud Database**
   * Confirm your Neon project exists and copy the pooled connection string.
3. **Step 3: Deploy Backend on Render**
   * Create **Web Service** pointing to your GitHub repository.
   * Set Root Directory to `backend`.
   * Set Build Command to `pip install -r requirements.txt`.
   * Set Start Command to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
   * Add Environment Variables: `DATABASE_URL` and `SECRET_KEY`.
   * Wait for deployment to finish and copy your live backend URL (`https://...onrender.com`).
   * Test `https://<backend-url>/api/health` $\rightarrow$ should return `"status": "healthy"`.
4. **Step 4: Deploy Frontend on Render**
   * Create **Static Site** pointing to your GitHub repository.
   * Set Root Directory to `frontend`.
   * Set Build Command to `npm install && npm run build`.
   * Set Publish Directory to `dist`.
   * Add Environment Variable: `VITE_API_URL = https://<your-backend-url>`.
   * Add Rewrite Rule: `/*` $\rightarrow$ `/index.html` (Rewrite).
5. **Step 5: Verify Live Application**
   * Open the live frontend URL in your browser.
   * Test user flow: Register new customer $\rightarrow$ Login $\rightarrow$ View products $\rightarrow$ Log in as admin $\rightarrow$ Add product $\rightarrow$ Add to cart $\rightarrow$ View cart.

---

# Ask the Store - Local Run and Render Deployment

This guide explains how to run the full application with the "Ask the Store" AI assistant on your local machine and how to deploy it live to Render.

### Beginner Vocabulary
* **Environment Variable**: A named setting stored outside of your code files so you can securely provide passwords and configuration keys without hardcoding them.
* **Deploy**: The action of packaging and uploading your application code to a remote cloud server so it runs continuously and is accessible over the internet.
* **Redeploy**: Rebuilding, updating, and restarting an already deployed cloud service with new code changes or updated environment settings.
* **Logs**: A live text readout stream displayed by a computer or server showing every event, startup step, incoming request, and error happening in real time.
* **Live**: A status badge on Render indicating your server successfully compiled, started without errors, and is actively ready to receive web traffic.

---

## PART 1 — RUN EVERYTHING LOCALLY FIRST

Follow these steps to run and test the complete application on your computer before touching the cloud.

### 1. Preparing the Backend

1. Open your terminal in the main project folder (`Ecommerce_single_new`).
   * You should see: A command prompt showing `PS C:\Users\...\Ecommerce_single_new>`.

2. Type `cd backend` and press `Enter`.
   * You should see: The prompt change to `PS C:\Users\...\Ecommerce_single_new\backend>`.

3. Type `.\.venv\Scripts\Activate.ps1` and press `Enter` to activate your virtual environment.
   * You should see: The green or white prefix `(.venv)` appear on the left side of your terminal line.

4. Type `pip install -r requirements.txt` and press `Enter` to install dependencies.
   * You should see: Download and installation messages finishing with `Successfully installed...` (or `Requirement already satisfied`).

5. Open the file `backend/.env` in your text editor.
   * You should see: The text contents of your local environment file.

6. Check that `backend/.env` contains all **7 required variable names** on separate lines with no extra spaces around the `=` sign:
   * `DATABASE_URL`
   * `SECRET_KEY`
   * `GROQ_API_KEY`
   * `GROQ_MODEL`
   * `LANGFUSE_PUBLIC_KEY`
   * `LANGFUSE_SECRET_KEY`
   * `LANGFUSE_HOST`
   * You should see: All 7 names present in the file with their respective configuration values.

7. In your backend terminal, type `uvicorn main:app --reload --port 8000` and press `Enter`.
   * You should see: Startup output concluding with `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`.

8. Open your browser and go to `http://127.0.0.1:8000/api/health`.
   * You should see: The JSON response `{"status":"healthy","database":"connected"}` on your screen.

---

### 2. Preparing and Testing the Frontend

9. Open a second, new terminal window in the main project folder (`Ecommerce_single_new`).
   * You should see: A fresh command prompt showing `PS C:\Users\...\Ecommerce_single_new>`.

10. Type `cd frontend` and press `Enter`.
    * You should see: The prompt change to `PS C:\Users\...\Ecommerce_single_new\frontend>`.

11. Type `npm run dev` and press `Enter`.
    * You should see: Output showing `VITE v8.3.4 ready in ... ms` and `Local: http://localhost:5173/`.

12. Open your web browser and go to `http://localhost:5173`.
    * You should see: The Simple Store homepage with the top navigation bar showing **Products**, **Cart**, **Chat**, and **Login**.

13. In the top navigation bar, click on **Register**.
    * You should see: The customer registration form.

14. Type a test email (e.g. `customer@example.com`), type a password (e.g. `Password123!`), and click **Register**.
    * You should see: A green success toast message and redirection to the login page.

15. On the login page, enter `customer@example.com`, enter `Password123!`, and click **Login**.
    * You should see: The navigation bar update to display `👤 customer@example.com` and a **Logout** button.

16. In the navigation bar, click on **Chat**.
    * You should see: The "Ask the Store" chat box with the heading `💬 Ask the Store` and a greeting message from the store assistant.

17. Type `What products are available in the store?` into the chat input and click **Send**.
    * You should see: A temporary `💭 Thinking...` status, followed by the assistant's answer listing the catalog items with their exact database prices.

18. In the navigation bar, click on **Logout**.
    * You should see: The navigation bar return to showing **Login** and **Register**.

19. In the navigation bar, click on **Login**.
    * You should see: The login screen.

20. Log in with the default administrator credentials: enter `admin@store.com`, enter `AdminPass123!`, and click **Login**.
    * You should see: The navigation bar display `👤 admin@store.com (Admin)` and the `+ Add Product` button.

21. In the navigation bar, click on **Chat**.
    * You should see: The chat screen active for the logged-in admin user.

22. Type `How much stock is left for the headphones?` into the chat input and click **Send**.
    * You should see: The assistant's answer stating that 15 units are available in stock.

23. Switch back to your second terminal (frontend) and press `Ctrl + C` to stop the dev server.
    * You should see: A prompt asking `Terminate batch job (Y/N)?` (type `Y` and press `Enter` if prompted) and the command line return.

24. Type `npm run build` and press `Enter` to test the production build.
    * You should see: `vite v8.3.4 building for production... ✓ built in ...ms` confirming there are zero JavaScript errors.

---

## PART 2 — DEPLOY ON RENDER

Follow these steps to deploy the updated application live to Render.

### 1. Pushing Code Securely to GitHub

25. In your terminal, type `cd ..` and press `Enter` to return to the main project root folder (`Ecommerce_single_new`).
    * You should see: `PS C:\Users\...\Ecommerce_single_new>`.

26. Type `git status` and press `Enter`.
    * You should see: Git output listing modified files (`DEPLOYMENT.md`, `backend/requirements.txt`, etc.) and confirming that `backend/.env` is **NOT** listed anywhere in untracked files.

27. Type `git add .` and press `Enter`.
    * You should see: The terminal prompt return silently, staging all updated files.

28. Type `git commit -m "Add Ask the Store agent, chat interface, and Langfuse tracing"` and press `Enter`.
    * You should see: A commit confirmation showing the files changed and insertions made.

29. Type `git push origin main` and press `Enter`.
    * You should see: Git transmission output ending with `To https://github.com/... [new branch/updated] main -> main`.

---

### 2. Updating the Backend Web Service on Render

30. Open your web browser and navigate to [dashboard.render.com](https://dashboard.render.com).
    * You should see: Your Render Dashboard listing your deployed services.

31. Click on your backend **Web Service** (e.g. `ecommerce-backend`).
    * You should see: The backend service overview page with tabs for Events, Logs, Metrics, Environment, and Settings.

32. In the left navigation menu, click on **Environment**.
    * You should see: The Environment Variables page showing existing entries for `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES`.

33. Click the **Add Environment Variable** button.
    * You should see: A new empty row with two input boxes: **Key** and **Value**.

34. In the **Key** box, type `GROQ_API_KEY`.
    * You should see: `GROQ_API_KEY` entered in the Key box.

35. In the **Value** box, paste your Groq API key (starts with `gsk_`).
    * You should see: Your key entered in the Value box.

36. Click the **Add Environment Variable** button again.
    * You should see: Another new empty Key and Value row appear.

37. In the **Key** box, type `GROQ_MODEL`.
    * You should see: `GROQ_MODEL` entered in the Key box.

38. In the **Value** box, type `llama-3.3-70b-versatile`.
    * You should see: `llama-3.3-70b-versatile` entered in the Value box.

39. Click the **Add Environment Variable** button again.
    * You should see: Another new empty Key and Value row appear.

40. In the **Key** box, type `LANGFUSE_PUBLIC_KEY`.
    * You should see: `LANGFUSE_PUBLIC_KEY` entered in the Key box.

41. In the **Value** box, paste your Langfuse Public Key (starts with `pk-lf-`).
    * You should see: Your public key entered in the Value box.

42. Click the **Add Environment Variable** button again.
    * You should see: Another new empty Key and Value row appear.

43. In the **Key** box, type `LANGFUSE_SECRET_KEY`.
    * You should see: `LANGFUSE_SECRET_KEY` entered in the Key box.

44. In the **Value** box, paste your Langfuse Secret Key (starts with `sk-lf-`).
    * You should see: Your secret key entered in the Value box.

45. Click the **Add Environment Variable** button again.
    * You should see: Another new empty Key and Value row appear.

46. In the **Key** box, type `LANGFUSE_HOST`.
    * You should see: `LANGFUSE_HOST` entered in the Key box.

47. In the **Value** box, type `https://cloud.langfuse.com` (or your regional host URL).
    * You should see: `https://cloud.langfuse.com` entered in the Value box.

48. Scroll down to the bottom of the page and click the **Save Changes** button.
    * You should see: A confirmation notification and an automatic redeployment triggered.

49. In the left navigation menu, click on **Logs**.
    * You should see: Real-time deployment logs showing `pip install -r requirements.txt`, packages installing (`langfuse`, `langgraph`, `langchain-groq`), and Uvicorn starting.

50. Wait until the status badge next to your service name at the top turns green and reads **Live**.
    * You should see: A green circular badge and the text **Live**.

51. *(Optional manual step)*: If an automatic deployment did not start after saving, click the **Manual Deploy** button at the top-right corner of the page and click **Deploy latest commit**.
    * You should see: A new build start running in the Logs tab until the status badge turns **Live**.

52. Find your public backend URL displayed directly below your service title at the top of the page (e.g. `https://ecommerce-backend.onrender.com`).
    * You should see: Your public backend HTTPS URL.

53. Open a new tab in your web browser, paste your backend URL, and add `/api/health` to the end (e.g. `https://ecommerce-backend.onrender.com/api/health`).
    * You should see: The JSON response `{"status":"healthy","database":"connected"}`.

---

### 3. Redeploying the Frontend Static Site on Render

54. In Render, click on **Dashboard** in the top navigation bar.
    * You should see: Your list of services.

55. Click on your frontend **Static Site** (e.g. `ecommerce-frontend`).
    * You should see: The frontend static site dashboard.

56. In the left navigation menu, click on **Environment**.
    * You should see: The Environment Variables list for your frontend.

57. Verify that `VITE_API_URL` is set to your live backend URL ending strictly in `/api` with no slash at the end (e.g. `https://ecommerce-backend.onrender.com/api`).
    * You should see: `VITE_API_URL` matching your backend URL ending in `/api` (do not change this value).

58. Look at the top-right corner of the page, click the **Manual Deploy** button, and click **Clear build cache & deploy**.
    * You should see: The build logs screen start running `npm install && npm run build` and compiling your React app.

59. Wait for the build to complete and the status badge at the top to change to green **Live**.
    * You should see: The green badge and the text **Live**.

60. Click on your public frontend URL displayed at the top of the page (e.g. `https://ecommerce-frontend.onrender.com`).
    * You should see: Your live e-commerce store loading in production with the **Chat** navigation link.

---

### 4. Testing the Live App and Langfuse Observability

61. On your live frontend website, click on **Login**.
    * You should see: The login screen.

62. Enter a registered normal user's email and password, and click **Login**.
    * You should see: Successful login toast and user email in the navigation bar.

63. Click on **Chat** in the navigation bar.
    * You should see: The "Ask the Store" chat interface loading.

64. Type `What products do you carry and what do they cost?` and click **Send**.
    * You should see: The live assistant reply listing the catalog products and prices from your Neon database.

65. Log out, then log in using your admin credentials (`admin@store.com` / `AdminPass123!`).
    * You should see: The navigation bar show `(Admin)`.

66. Click on **Chat** as admin and ask `What is the stock level of the smartwatch?`.
    * You should see: The live assistant reply confirming 10 units in stock.

67. Open a new browser tab and navigate to [cloud.langfuse.com](https://cloud.langfuse.com).
    * You should see: Your Langfuse project dashboard.

68. In the left navigation sidebar, click on **Tracing**.
    * You should see: Live trace entries named `ask-the-store-flow` logged for the questions you just asked on your live production site.

69. Click on any trace row.
    * You should see: The complete trace details panel displaying the user question, the database read step, the Groq LLM call, latency timing, and the final answer.

---

### 5. How to Roll Back a Deployment

If an update ever causes an issue in production, you can immediately roll back to your previous working release:

70. In the Render Dashboard, click on the affected service (Web Service or Static Site).
    * You should see: The service overview.

71. In the left navigation menu, click on **Deploys** (or **Events**).
    * You should see: A chronological history list of all past builds and deployments.

72. Find the previous deployment that was working successfully.

73. Click the three dots icon (`...`) on the right side of that deployment row.
    * You should see: A dropdown menu with options including **Rollback to this deploy**.

74. Click **Rollback to this deploy**.
    * You should see: Render immediately switch production traffic back to that working release.

---

### 6. Free Plan Note: Cold Starts

> [!NOTE]
> On Render's free tier, Web Services automatically spin down (go to sleep) after **15 minutes of inactivity** to conserve server resources.
> When a user visits your site after it has been sleeping, Render spins up the container from scratch. This "cold start" takes **30 to 60 seconds**.
> If your very first chat question shows "Thinking..." for up to a minute, this is completely normal behavior on the free plan while the server wakes up. All subsequent requests while active will respond in 1 to 2 seconds.

---

## If Something Goes Wrong

* **Render shows "Failed"**:
  * Click on the **Logs** tab of your service in Render.
  * Look at the red error lines near the bottom of the log.
  * Common causes: A typo in an environment variable name, an extra space in `backend/.env`, or a missing package in `backend/requirements.txt`.

* **`ModuleNotFoundError` (e.g. `No module named 'langfuse'` or `'langchain_groq'`)**:
  * You forgot to add the dependency to `backend/requirements.txt` or did not push `requirements.txt` to GitHub.
  * Verify `requirements.txt` contains `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`, `python-dotenv`, `pydantic`, `pyjwt`, `bcrypt`, `langgraph`, `langchain-groq`, and `langfuse`. Commit and push to GitHub.

* **`/health` not connected (`"database": "disconnected"`)**:
  * The backend cannot connect to your Neon PostgreSQL database.
  * In the Render backend **Environment** tab, check `DATABASE_URL`.
  * Ensure the string starts with `postgresql+psycopg://` and ends with `?sslmode=require`.

* **Model not available or Groq limit reached (503 Service Unavailable)**:
  * Check the Render backend **Environment** tab to ensure `GROQ_API_KEY` is present and matches the key from [console.groq.com](https://console.groq.com).
  * If using Groq's free tier, you may have reached the per-minute token limit. Wait 60 seconds and submit your question again.

* **Chat not loading answers (stuck on "Thinking..." or network error)**:
  * In your Render frontend Static Site **Environment** tab, ensure `VITE_API_URL` is set to `<your-backend-url>/api` (e.g. `https://ecommerce-backend.onrender.com/api`).
  * If you updated `VITE_API_URL`, you must click **Manual Deploy** $\rightarrow$ **Clear build cache & deploy** because Vite only bakes environment variables into JavaScript files during the build phase.

* **No traces appear in Langfuse**:
  * In your Render backend **Environment** tab, verify that `LANGFUSE_PUBLIC_KEY` starts with `pk-lf-`, `LANGFUSE_SECRET_KEY` starts with `sk-lf-`, and `LANGFUSE_HOST` is set to `https://cloud.langfuse.com` (or your regional URL).
  * Ensure there are no quotation marks (`"`) or whitespace characters around the keys.
  * Save changes and verify in **Logs** that the service redeployed.

