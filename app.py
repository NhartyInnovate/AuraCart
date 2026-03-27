from flask import Flask, render_template, session, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import requests
import os
import uuid
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DATABASE = "store.db"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

UPLOAD_FOLDER = os.path.join("static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT,
            category TEXT,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total_amount INTEGER NOT NULL,
            payment_reference TEXT NOT NULL UNIQUE,
            payment_status TEXT NOT NULL,
            order_status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            image TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    """)

    conn.commit()
    conn.close()

def ensure_order_status_column():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]

    if "order_status" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN order_status TEXT NOT NULL DEFAULT 'Pending'")
        conn.commit()

    conn.close()


def seed_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    if count == 0:
        # only seed if empty
        cursor.execute("""
            INSERT INTO products (name, price, image, description, category, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Sample Perfume", 15000, "perfume1.webp", "Luxury scent", "Men", 10))

        conn.commit()

    conn.close()
def get_all_products():
    conn = get_db_connection()
    products = conn.execute("""
        SELECT * FROM products
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return products


def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute("""
        SELECT * FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()
    conn.close()
    return product


def save_order(order_data, cart):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (customer_name, email, phone, address, total_amount, payment_reference, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        order_data["customer_name"],
        order_data["email"],
        order_data["phone"],
        order_data["address"],
        order_data["total"],
        order_data["reference"],
        "paid"
    ))

    order_id = cursor.lastrowid

    for item in cart.values():
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, price, quantity, image)
            VALUES (?, ?, ?, ?, ?)
        """, (
            order_id,
            item["name"],
            item["price"],
            item["quantity"],
            item["image"]
        ))

    conn.commit()
    conn.close()

def add_product_to_db(name, description, price, image, category, stock):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO products (name, description, price, image, category, stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, price, image, category, stock))
    conn.commit()
    conn.close()


def update_product_in_db(product_id, name, description, price, image, category, stock):
    conn = get_db_connection()
    conn.execute("""
        UPDATE products
        SET name = ?, description = ?, price = ?, image = ?, category = ?, stock = ?
        WHERE id = ?
    """, (name, description, price, image, category, stock, product_id))
    conn.commit()
    conn.close()


def delete_product_from_db(product_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def get_all_orders():
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT * FROM orders
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return orders


def get_order_items(order_id):
    conn = get_db_connection()
    items = conn.execute("""
        SELECT * FROM order_items
        WHERE order_id = ?
    """, (order_id,)).fetchall()
    conn.close()
    return items

def update_order_status(order_id, new_status):
    conn = get_db_connection()
    conn.execute("""
        UPDATE orders
        SET order_status = ?
        WHERE id = ?
    """, (new_status, order_id))
    conn.commit()
    conn.close()

def get_product(product_id):
    products = get_all_products()
    return next((product for product in products if product["id"] == product_id), None)


def get_cart_total(cart):
    return sum(item["price"] * item["quantity"] for item in cart.values())

def get_cart_item_count(cart):
    return sum(item["quantity"] for item in cart.values())

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        counter += 1

    file.save(filepath)
    return filename


@app.route("/")
def home():
    products = get_all_products()
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return "Product not found", 404
    return render_template("product.html", product=product)


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product:
        return "Product not found", 404

    cart = session.get("cart", {})
    product_id_str = str(product_id)

    current_quantity = cart.get(product_id_str, {}).get("quantity", 0)

    if current_quantity < product["stock"]:
        if product_id_str in cart:
            cart[product_id_str]["quantity"] += 1
        else:
            cart[product_id_str] = {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "image": product["image"],
                "quantity": 1
            }
    else:
        flash("Cannot add more than available stock.", "warning")

    session["cart"] = cart
    return redirect(url_for("cart"))



@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    total = get_cart_total(cart)
    item_count = get_cart_item_count(cart)
    return render_template("cart.html", cart=cart, total=total, item_count=item_count)

@app.route("/update_cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    cart = session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        quantity = int(request.form.get("quantity", 1))

        if quantity <= 0:
            cart.pop(product_id_str)
        else:
            cart[product_id_str]["quantity"] = quantity

        session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart.pop(product_id_str)
        session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    total = get_cart_total(cart)

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not customer_name or not email or not phone or not address:
            error = "Please fill in all fields."
            return render_template(
                "checkout.html",
                cart=cart,
                total=total,
                error=error,
                form_data={
                    "customer_name": customer_name,
                    "email": email,
                    "phone": phone,
                    "address": address
                }
            )

        reference = f"AURACART-{uuid.uuid4().hex[:12].upper()}"

        order_data = {
            "customer_name": customer_name,
            "email": email,
            "phone": phone,
            "address": address,
            "total": total,
            "reference": reference
        }

        session["order_data"] = order_data
        return redirect(url_for("initialize_payment"))

    return render_template(
        "checkout.html",
        cart=cart,
        total=total,
        error=None,
        form_data={}
    )


@app.route("/initialize_payment")
def initialize_payment():
    order_data = session.get("order_data")
    if not order_data:
        return redirect(url_for("checkout"))

    if not PAYSTACK_SECRET_KEY:
        flash("Paystack secret key is missing.", "danger")
        return redirect(url_for("checkout"))

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": order_data["email"],
        "amount": order_data["total"] * 100,
        "reference": order_data["reference"],
        "callback_url": f"{BASE_URL}/verify_payment",
        "metadata": {
            "customer_name": order_data["customer_name"],
            "phone": order_data["phone"],
            "address": order_data["address"]
        }
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=20
        )
        data = response.json()
    except requests.RequestException:
        flash("Unable to connect to Paystack. Please try again.", "danger")
        return redirect(url_for("checkout"))

    if response.status_code == 200 and data.get("status"):
        return redirect(data["data"]["authorization_url"])

    flash("Unable to initialize payment. Please try again.", "danger")
    return redirect(url_for("checkout"))


@app.route("/verify_payment")
def verify_payment():
    reference = request.args.get("reference")
    if not reference:
        flash("Missing payment reference.", "danger")
        return redirect(url_for("checkout"))

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=20
        )
        data = response.json()
    except requests.RequestException:
        flash("Unable to verify payment at the moment.", "danger")
        return redirect(url_for("checkout"))

    if response.status_code == 200 and data.get("status"):
        transaction = data.get("data", {})
        if transaction.get("status") == "success":
            order_data = session.get("order_data")
            cart = session.get("cart", {})

            if not order_data:
                return redirect(url_for("home"))

            try:
                save_order(order_data, cart)
                reduce_stock_after_order(cart)
            except sqlite3.IntegrityError:
                flash("This payment has already been recorded.", "warning")
                return redirect(url_for("home"))

            session["paid_order"] = order_data
            session["paid_cart"] = cart

            session.pop("cart", None)
            session.pop("order_data", None)

            return redirect(url_for("success"))

    flash("Payment could not be verified.", "danger")
    return redirect(url_for("checkout"))


@app.route("/success")
def success():
    order_data = session.get("paid_order")
    cart = session.get("paid_cart", {})

    if not order_data:
        return redirect(url_for("home"))

    session.pop("paid_order", None)
    session.pop("paid_cart", None)

    return render_template("success.html", order_data=order_data, cart=cart)

def reduce_stock_after_order(cart):
    conn = get_db_connection()
    cursor = conn.cursor()

    for item in cart.values():
        cursor.execute("""
            UPDATE products
            SET stock = CASE
                WHEN stock - ? < 0 THEN 0
                ELSE stock - ?
            END
            WHERE id = ?
        """, (item["quantity"], item["quantity"], item["id"]))

    conn.commit()
    conn.close()


@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    orders = get_all_orders()

    orders_with_items = []
    for order in orders:
        items = get_order_items(order["id"])
        orders_with_items.append({
            "order": order,
            "order_items": items
        })

    return render_template("admin.html", orders_with_items=orders_with_items)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Please enter both username and password."
            return render_template("admin_login.html", error=error)

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Invalid credentials"
            return render_template("admin_login.html", error=error)

    return render_template("admin_login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/products")
def admin_products():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    products = get_all_products()
    return render_template("admin_products.html", products=products)


@app.route("/admin/products/add", methods=["GET", "POST"])
def admin_add_product():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        category = request.form.get("category", "").strip()
        stock = request.form.get("stock", "").strip()

        image_file = request.files.get("image")
        image_filename = save_uploaded_file(image_file)

        if not name or not description or not price or not category or not stock or not image_filename:
            error = "Please fill in all fields and upload a valid image."
            return render_template("admin_product_form.html", error=error, product=None, action="Add")

        add_product_to_db(
            name=name,
            description=description,
            price=int(price),
            image=image_filename,
            category=category,
            stock=int(stock)
        )

        return redirect(url_for("admin_products"))

    return render_template("admin_product_form.html", error=None, product=None, action="Add")


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    product = get_product(product_id)
    if not product:
        return "Product not found", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        category = request.form.get("category", "").strip()
        stock = request.form.get("stock", "").strip()

        image_file = request.files.get("image")
        uploaded_image = save_uploaded_file(image_file)
        image_filename = uploaded_image if uploaded_image else product["image"]

        if not name or not description or not price or not category or not stock:
            error = "Please fill in all required fields."
            return render_template("admin_product_form.html", error=error, product=product, action="Edit")

        update_product_in_db(
            product_id=product_id,
            name=name,
            description=description,
            price=int(price),
            image=image_filename,
            category=category,
            stock=int(stock)
        )

        return redirect(url_for("admin_products"))

    return render_template("admin_product_form.html", error=None, product=product, action="Edit")


@app.route("/admin/products/delete/<int:product_id>")
def admin_delete_product(product_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    delete_product_from_db(product_id)
    return redirect(url_for("admin_products"))



@app.route("/admin/orders/update-status/<int:order_id>", methods=["POST"])
def admin_update_order_status(order_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    new_status = request.form.get("order_status", "").strip()

    allowed_statuses = ["Pending", "Paid", "Shipped", "Delivered"]
    if new_status in allowed_statuses:
        update_order_status(order_id, new_status)

    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    ensure_order_status_column()
    seed_products()
    app.run(debug=True)
else:
    init_db()
    ensure_order_status_column()
    seed_products()