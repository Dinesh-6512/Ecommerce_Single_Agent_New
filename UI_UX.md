# UI/UX Specification Document

This document defines the layout and user experience for the 5 simple screens in our e-commerce application.

---

## Global Navigation Bar (Header)
Visible at the top of every screen:
* **Logo / App Name**: "Simple Store" (clicking takes you to Home).
* **Navigation Links**:
  * If NOT logged in: "Login", "Register".
  * If Logged in: "Products", "Cart", "Add Product", "Logout".

---

## 1. Register Screen (`/register`)

### What the user sees:
* A centered, clean form card.
* Title: **"Create an Account"**.
* Input fields:
  * Email
  * Password
* Button: **"Register"**.
* A helper link: *"Already have an account? Login here"*.
* Error or success message area (e.g., "Registration successful! Please log in.").

### What the user can do:
* Type an email and password.
* Click the "Register" button.

### Where the user goes next:
* On successful registration, redirected to the **Login Screen**.
* Clicking the helper link navigates to the **Login Screen**.

---

## 2. Login Screen (`/login`)

### What the user sees:
* A centered, clean form card.
* Title: **"Welcome Back - Login"**.
* Input fields:
  * Email
  * Password
* Button: **"Login"**.
* A helper link: *"Don't have an account? Register here"*.
* Error message area (e.g., "Invalid email or password").

### What the user can do:
* Enter registered email and password.
* Click the "Login" button.

### Where the user goes next:
* On successful login, the authentication token is saved in the browser, and the user is redirected to the **Home / Product Listing Screen**.
* Clicking the helper link navigates to the **Register Screen**.

---

## 3. Home / Product Listing Screen (`/`)

### What the user sees:
* A welcoming headline: **"Available Products"**.
* A clean grid of product cards.
* Each product card displays:
  * Product image
  * Product title
  * Price (e.g., "$19.99")
  * Short description
  * A button: **"Add to Cart"**
* If no products exist: A message *"No products available yet. Click 'Add Product' to add one."*

### What the user can do:
* Scroll through the list of products.
* Click **"Add to Cart"** on any product card.
* Click **"Cart"** in the top navigation bar to check selected items.

### Where the user goes next:
* Clicking "Add to Cart" saves the item and shows a quick notice: *"Item added to cart!"* (user stays on this page).
* Clicking "Cart" in the navbar navigates to the **Cart Screen**.
* Clicking "Add Product" in the navbar navigates to the **Add Product Screen**.

---

## 4. Cart Screen (`/cart`)

### What the user sees:
* Page title: **"My Shopping Cart"**.
* A simple list or table showing all items added by the current user:
  * Product name
  * Product price
* Cart total summary: **Total: $XX.XX**.
* If cart is empty: A message *"Your cart is empty. Browse products to add items."* with a button: **"Back to Products"**.

### What the user can do:
* View all items currently saved in their cart.
* View the combined total cost of the items.
* Click navigation links to continue browsing.

### Where the user goes next:
* Clicking **"Products"** in the navbar or the "Back to Products" button returns the user to the **Home / Product Listing Screen**.

---

## 5. Add Product Screen (`/add-product`)

### What the user sees:
* A centered form card.
* Title: **"Add New Product"**.
* Input fields:
  * Product Title (text input)
  * Price (number input)
  * Image URL (text input)
  * Description (textarea)
* Button: **"Save Product"**.
* Success or error message area.

### What the user can do:
* Enter the product details.
* Click the **"Save Product"** button.

### Where the user goes next:
* On successful save, a message appears: *"Product created successfully!"*, and the user is redirected to the **Home / Product Listing Screen** where the newly added product is immediately visible.
