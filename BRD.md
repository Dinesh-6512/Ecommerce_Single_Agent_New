# Business Requirements Document (BRD)

## 1. Project Goal
Build a minimal, working full-stack e-commerce web application to learn how ReactJS (frontend), FastAPI (backend), and Neon PostgreSQL (cloud database) connect and work together.

---

## 2. Target Users
* **Customer**: A shopper who browses items, registers/logs in, and adds items to their shopping cart.
* **Admin**: A store manager who can add new products to the catalog.

---

## 3. Main User Journey

### Customer Journey:
1. **Visit Site**: Open the application in a browser.
2. **Register / Login**: Create a new account or log in with email and password.
3. **View Products**: See the list of available items (title, price, image URL, description).
4. **Add to Cart**: Click "Add to Cart" on a product.
5. **View Cart**: Open the cart page to view all selected items.

### Admin Journey:
1. **Add Product**: Fill in a simple form (name, price, description, image URL) and save the product to the store.

---

## 4. In Scope (Features to Build)

### Customer Features (Only These):
1. **User Registration**: Create a customer account (email and password).
2. **User Login**: Log in to receive an authentication token.
3. **View Products**: Display a grid of all available products.
4. **Add Product to Cart**: Add any product to the customer's cart.
5. **View Cart**: Display items currently in the customer's cart.

### Admin Features (Only This):
1. **Add Product**: Simple form to create and save a new product into the catalog.

---

## 5. Out of Scope (Do NOT Build)
To keep the project simple and focused, the following features will **not** be built:
* Product search
* Dedicated product details page
* Product categories or tags
* Edit or delete products
* Change item quantity in cart
* Remove item from cart
* Checkout and payment gateway
* Order placement and order tracking
* Order history
* User profile editing
* Separate dedicated admin dashboard / panel

---

## 6. Simple Success Criteria
1. A new user can register and log in successfully.
2. An admin can add a new product and see it appear in the database.
3. A logged-in customer can view all products.
4. A customer can click "Add to Cart" and see that item appear in their cart view.
5. All data (users, products, cart items) is stored and retrieved from the Neon PostgreSQL cloud database.
