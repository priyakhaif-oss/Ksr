from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "ksr_dairy_secret_key"

# Products Data
PRODUCTS = [
    {
        "id": 1,
        "name": "Cow Milk",
        "price": 60,
        "image": "cow-milk.jpg",
        "description": "Fresh pure cow milk"
    },
    {
        "id": 2,
        "name": "Buffalo Milk",
        "price": 80,
        "image": "buffalo-milk.jpg",
        "description": "Rich and creamy buffalo milk"
    },
    {
        "id": 3,
        "name": "Premium Buffalo Milk",
        "price": 90,
        "image": "premium-buffalo.jpg",
        "description": "Premium quality buffalo milk"
    }
]


@app.route("/")
def home():
    return render_template(
        "index.html",
        products=PRODUCTS
    )


# Add product to cart
@app.route("/add-cart", methods=["POST"])
def add_cart():

    product_id = int(request.form.get("product_id"))

    cart = session.get("cart", [])

    found = False

    for item in cart:
        if item["id"] == product_id:
            item["qty"] += 1
            found = True
            break

    if not found:
        for product in PRODUCTS:
            if product["id"] == product_id:
                cart.append({
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "image": product["image"],
                    "qty": 1
                })

    session["cart"] = cart

    return jsonify({
        "status": "success",
        "message": "Added to cart"
    })


# Cart page
@app.route("/cart")
def cart():

    cart = session.get("cart", [])

    total = sum(
        item["price"] * item["qty"]
        for item in cart
    )

    return render_template(
        "cart.html",
        cart=cart,
        total=total
    )


# Remove cart item
@app.route("/remove/<int:id>")
def remove(id):

    cart = session.get("cart", [])

    cart = [
        item for item in cart
        if item["id"] != id
    ]

    session["cart"] = cart

    return render_template(
        "cart.html",
        cart=cart,
        total=sum(
            item["price"] * item["qty"]
            for item in cart
        )
    )


# Checkout
@app.route("/checkout")
def checkout():

    cart = session.get("cart", [])

    total = sum(
        item["price"] * item["qty"]
        for item in cart
    )

    return render_template(
        "checkout.html",
        cart=cart,
        total=total
    )


# Place order
@app.route("/place-order", methods=["POST"])
def place_order():

    name = request.form.get("name")
    phone = request.form.get("phone")
    address = request.form.get("address")

    order = {
        "name": name,
        "phone": phone,
        "address": address,
        "date": datetime.now()
    }

    print(order)

    session.clear()

    return render_template(
        "success.html"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
)
