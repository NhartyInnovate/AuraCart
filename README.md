# 🛍️ AuraCart

AuraCart is a modern, full-stack e-commerce web application built with Flask, designed to deliver a seamless shopping experience with integrated payments, inventory management, and an admin control system.

🚀 Live Demo: (https://auracart-d854.onrender.com/)

---

## ✨ Features

### 🛒 Customer Experience
- Browse products with a clean, premium UI
- Add to cart with real-time updates
- Dynamic cart summary (auto updates)
- Smooth checkout experience
- Paystack payment integration
- Order success confirmation page

### 🔐 Admin Dashboard
- Secure admin login system
- View all customer orders
- Update order status:
  - Pending
  - Paid
  - Shipped
  - Delivered
- Manage products:
  - Add / Edit / Delete products
- Inventory tracking
- Low stock alerts

### 📊 Smart System Features
- Automatic stock reduction after purchase
- Prevents adding items beyond available stock
- Dashboard summary:
  - Total Orders
  - Revenue
  - Total Products
  - Low Stock Count
- Order filtering by status

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, Bootstrap
- **Database:** SQLite (for demo)
- **Payments:** Paystack API
- **Deployment:** Render
- **Version Control:** Git & GitHub

---

## ⚙️ Installation (Local Setup)

```bash
git clone https://github.com/your-username/auracart.git
cd auracart

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt

Create a .env file:

SECRET_KEY=your_secret_key
PAYSTACK_SECRET_KEY=your_paystack_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your_hashed_password
BASE_URL=http://127.0.0.1:5000

Run the app:

python app.py


---

🔑 Admin Access

Admin login route:

/admin/login

Admin dashboard appears after login.


---

🚀 Deployment

Deployed on Render using:

Build Command:


pip install -r requirements.txt

Start Command:


gunicorn app:app


---

⚠️ Notes

SQLite is used for demonstration purposes

Uploaded images and database may reset on redeploy (Render free tier)

Recommended upgrades:

PostgreSQL (production DB)

Cloud storage (for images)


---

📌 Future Improvements

Customer authentication system

Email notifications

Analytics dashboard (charts)

Cloud image storage

Order tracking for customers



---
