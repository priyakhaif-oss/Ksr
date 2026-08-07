from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime
import os

from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId


load_dotenv()


app = Flask(__name__)

app.secret_key = "ksr_dairy_secret_key"



# ================= BRANDING =================

SITE_NAME = "KSR Dairy Foods"

SITE_TAGLINE = "Fresh Milk Delivered To Your Doorstep"



@app.context_processor
def inject_brand():

    cart = session.get("cart", [])

    cart_count = sum(
        item["qty"]
        for item in cart
    )

    return {

        "site_name": SITE_NAME,

        "site_tagline": SITE_TAGLINE,

        "cart_count": cart_count

    }





# ================= ADMIN LOGIN =================

ADMIN_USERNAME = "ksr"

ADMIN_PASSWORD = "123"





# ================= MONGODB =================

mongo_uri = os.environ.get("MONGO_URI")



def get_orders_collection():

    client = MongoClient(mongo_uri)

    db = client["ksr_dairy"]

    return db["orders"]





# ================= PRODUCTS =================

PRODUCTS = [


    {
        "id":1,

        "name":"Cow Milk",

        "price":60,

        "image":"/static/images/cow-milk.jpg",

        "description":"Fresh pure cow milk"

    },


    {
        "id":2,

        "name":"Buffalo Milk",

        "price":80,

        "image":"/static/images/buffalo-milk.jpg",

        "description":"Rich and creamy buffalo milk"

    },


    {
        "id":3,

        "name":"Premium Buffalo Milk",

        "price":90,

        "image":"/static/images/premium-milk.jpg",

        "description":"Premium quality buffalo milk"

    }


]





# ================= HOME =================

@app.route("/")
def home():


    return render_template(

        "index.html",

        products=PRODUCTS

    )





# ================= CART =================

@app.route("/add-cart", methods=["POST"])
def add_cart():


    product_id = int(
        request.form.get("product_id")
    )


    cart = session.get(
        "cart",
        []
    )



    for item in cart:


        if item["id"] == product_id:


            item["qty"] += 1

            break



    else:


        for product in PRODUCTS:


            if product["id"] == product_id:


                cart.append({

                    "id":product["id"],

                    "name":product["name"],

                    "price":product["price"],

                    "image":product["image"],

                    "qty":1

                })


                break



    session["cart"] = cart



    return jsonify({

        "status":"success",

        "message":"Added to cart"

    })


# ================= CART MANAGEMENT =================


@app.route("/cart")
def cart():

    return cart_page()





@app.route("/increase/<int:id>")
def increase(id):


    cart = session.get(
        "cart",
        []
    )


    for item in cart:


        if item["id"] == id:


            item["qty"] += 1

            break



    session["cart"] = cart


    return cart_page()





@app.route("/decrease/<int:id>")
def decrease(id):


    cart = session.get(
        "cart",
        []
    )



    for item in cart:


        if item["id"] == id:



            if item["qty"] > 1:


                item["qty"] -= 1


            else:


                cart.remove(item)



            break




    session["cart"] = cart


    return cart_page()





@app.route("/remove/<int:id>")
def remove(id):


    cart = session.get(
        "cart",
        []
    )



    cart = [

        item

        for item in cart

        if item["id"] != id

    ]



    session["cart"] = cart



    return cart_page()





def cart_page():


    cart = session.get(
        "cart",
        []
    )



    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )



    return render_template(

        "cart.html",

        cart=cart,

        total=total

    )







# ================= CHECKOUT =================


@app.route("/checkout")
def checkout():


    cart = session.get(
        "cart",
        []
    )



    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )



    return render_template(

        "checkout.html",

        cart=cart,

        total=total

    )






# ================= ORDER PLACE =================


@app.route("/place-order", methods=["POST"])
def place_order():


    cart = session.get(
        "cart",
        []
    )



    if not cart:


        return redirect("/")



    phone = request.form.get(
        "phone"
    )



    if not phone.isdigit() or len(phone) != 10:


        return render_template(

            "checkout.html",

            cart=cart,

            total=sum(

                item["price"] * item["qty"]

                for item in cart

            ),

            error="Enter valid 10 digit mobile number"

        )



    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )



    order = {


        "name":
        request.form.get("name"),


        "phone":
        phone,


        "address":
        request.form.get("address"),


        "products":
        cart,


        "total":
        total,


        "status":
        "Pending",


        "date":
        datetime.now()


    }



    get_orders_collection().insert_one(order)



    session.clear()



    return render_template(

        "success.html"

    )


# ================= ADMIN PANEL =================


@app.route("/admin")
def admin():


    if not session.get("admin"):


        return render_template(

            "admin_login.html"

        )



    orders = list(

        get_orders_collection()

        .find()

        .sort(

            "date",

            -1

        )

    )



    total_orders = len(orders)



    pending_orders = len([

        order

        for order in orders

        if order.get("status") == "Pending"

    ])




    delivered_orders = len([

        order

        for order in orders

        if order.get("status") == "Delivered"

    ])





    return render_template(

        "admin.html",


        orders=orders,


        total_orders=total_orders,


        pending_orders=pending_orders,


        delivered_orders=delivered_orders

    )







# ================= ADMIN LOGIN =================


@app.route("/admin-login", methods=["POST"])
def admin_login():


    username = request.form.get(
        "username"
    )


    password = request.form.get(
        "password"
    )



    if (

        username == ADMIN_USERNAME

        and

        password == ADMIN_PASSWORD

    ):


        session["admin"] = True



        return redirect("/admin")




    return render_template(

        "admin_login.html",


        error="Invalid Username or Password"

    )







# ================= ADMIN LOGOUT =================


@app.route("/admin-logout")
def admin_logout():


    session.pop(

        "admin",

        None

    )


    return redirect("/admin")







# ================= UPDATE ORDER STATUS =================


@app.route("/update-status/<id>/<status>")
def update_status(id,status):


    get_orders_collection().update_one(


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







# ================= DELETE ORDER =================


@app.route("/delete-order/<id>")
def delete_order(id):


    get_orders_collection().delete_one(


        {

            "_id":ObjectId(id)

        }


    )


    return redirect("/admin")



# ================= ERROR HANDLING =================


@app.errorhandler(404)
def page_not_found(error):

    return render_template(

        "404.html"

    ),404





@app.errorhandler(500)
def server_error(error):

    return render_template(

        "500.html"

    ),500







# ================= SESSION SETTINGS =================


@app.before_request
def keep_session_alive():

    session.permanent = True





# ================= API CART COUNT =================


@app.route("/cart-count")
def cart_count():


    cart = session.get(

        "cart",

        []

    )


    count = sum(

        item["qty"]

        for item in cart

    )


    return jsonify({

        "count":count

    })







# ================= HEALTH CHECK =================


@app.route("/health")
def health():


    return jsonify({

        "status":"KSR Dairy Foods is running"

    })



# ================= RUN SERVER =================


if __name__ == "__main__":


    port = int(

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


