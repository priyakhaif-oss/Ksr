from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime
import os

from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId


load_dotenv()


app = Flask(__name__)

app.secret_key = "ksr_dairy_secret_key"



# Admin Login

ADMIN_USERNAME = "ksr"
ADMIN_PASSWORD = "123"





# MongoDB Setup

mongo_uri = os.environ.get("MONGO_URI")

client = MongoClient(mongo_uri)

db = client["ksr_dairy"]

orders_collection = db["orders"]





# Products Data

PRODUCTS = [

    {
        "id": 1,
        "name": "Cow Milk",
        "price": 60,
        "image": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600",
        "description": "Fresh pure cow milk"
    },

    {
        "id": 2,
        "name": "Buffalo Milk",
        "price": 80,
        "image": "https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=600",
        "description": "Rich and creamy buffalo milk"
    },

    {
        "id": 3,
        "name": "Premium Buffalo Milk",
        "price": 90,
        "image": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=600",
        "description": "Premium quality buffalo milk"
    }

]






@app.route("/")
def home():

    return render_template(
        "index.html",
        products=PRODUCTS
    )






# Add Cart

@app.route("/add-cart", methods=["POST"])
def add_cart():

    product_id = int(request.form.get("product_id"))

    cart = session.get("cart", [])


    for item in cart:

        if item["id"] == product_id:

            item["qty"] += 1
            break


    else:

        for product in PRODUCTS:

            if product["id"] == product_id:

                cart.append({

                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "image": product["image"],
                    "qty": 1

                })

                break



    session["cart"] = cart


    return jsonify({

        "status":"success",
        "message":"Added to cart"

    })






# Cart

@app.route("/cart")
def cart():

    return cart_page()






@app.route("/increase/<int:id>")
def increase(id):

    cart=session.get("cart",[])


    for item in cart:

        if item["id"]==id:

            item["qty"] += 1
            break


    session["cart"]=cart


    return cart_page()






@app.route("/decrease/<int:id>")
def decrease(id):

    cart=session.get("cart",[])


    for item in cart:

        if item["id"]==id:

            if item["qty"]>1:

                item["qty"]-=1

            else:

                cart.remove(item)

            break


    session["cart"]=cart


    return cart_page()






@app.route("/remove/<int:id>")
def remove(id):

    cart=session.get("cart",[])


    cart=[

        item for item in cart

        if item["id"] != id

    ]


    session["cart"]=cart


    return cart_page()






def cart_page():

    cart=session.get("cart",[])


    total=sum(

        item["price"]*item["qty"]

        for item in cart

    )


    return render_template(

        "cart.html",

        cart=cart,

        total=total

    )






# Checkout

@app.route("/checkout")
def checkout():

    cart=session.get("cart",[])


    total=sum(

        item["price"]*item["qty"]

        for item in cart

    )


    return render_template(

        "checkout.html",

        cart=cart,

        total=total

    )







# Place Order

@app.route("/place-order", methods=["POST"])
def place_order():


    cart=session.get("cart",[])


    total=sum(

        item["price"]*item["qty"]

        for item in cart

    )


    order={


        "name":request.form.get("name"),

        "phone":request.form.get("phone"),

        "address":request.form.get("address"),

        "products":cart,

        "total":total,

        "status":"Pending",

        "date":datetime.now()

    }



    orders_collection.insert_one(order)



    session.clear()



    return render_template(
        "success.html"
    )








# ================= ADMIN =================


@app.route("/admin")
def admin():


    if not session.get("admin"):

        return render_template(
            "admin_login.html"
        )


    orders=list(

        orders_collection.find().sort(
            "date",
            -1
        )

    )


    return render_template(

        "admin.html",

        orders=orders

    )






@app.route("/admin-login", methods=["POST"])
def admin_login():


    username=request.form.get("username")

    password=request.form.get("password")



    if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:


        session["admin"]=True


        return redirect("/admin")



    return render_template(

        "admin_login.html",

        error="Invalid Username or Password ❌"

    )






@app.route("/admin-logout")
def admin_logout():

    session.pop("admin",None)


    return redirect("/admin")







@app.route("/update-status/<id>/<status>")
def update_status(id,status):


    orders_collection.update_one(

        {
            "_id":ObjectId(id)
        },

        {
            "$set":{
                "status":status
            }
        }

    )


    return redirect("/admin")







if __name__=="__main__":


    port=int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=True

    )
