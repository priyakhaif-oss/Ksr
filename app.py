from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime, timedelta
import os

from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId


load_dotenv()



# ================= APP CONFIG =================

app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ksr_dairy_secret_key"
)


app.permanent_session_lifetime = timedelta(
    days=7
)





# ================= BRANDING =================

SITE_NAME = "KSR Dairy Foods"

SITE_TAGLINE = "Fresh Milk Delivered To Your Doorstep"





@app.context_processor
def inject_brand():


    cart = session.get(
        "cart",
        []
    )


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






# ================= DATABASE =================

mongo_uri = os.environ.get(
    "MONGO_URI"
)





def get_database():

    client = MongoClient(
        mongo_uri
    )

    return client["ksr_dairy"]





def get_orders_collection():

    db = get_database()

    return db["orders"]





def get_products_collection():

    db = get_database()

    return db["products"]





# ================= PRODUCTS =================


DEFAULT_PRODUCTS = [


    {

        "name":"Cow Milk",

        "price":60,

        "image":"/static/images/cow-milk.jpg",

        "description":"Fresh pure cow milk"

    },


    {

        "name":"Buffalo Milk",

        "price":80,

        "image":"/static/images/buffalo-milk.jpg",

        "description":"Rich and creamy buffalo milk"

    },


    {

        "name":"Premium Buffalo Milk",

        "price":90,

        "image":"/static/images/premium-milk.jpg",

        "description":"Premium quality buffalo milk"

    }


]






def get_all_products():


    products = list(

        get_products_collection()

        .find()

    )


    return products






def create_default_products():


    collection = get_products_collection()



    if collection.count_documents({}) == 0:


        collection.insert_many(
            DEFAULT_PRODUCTS
        )





# ================= CATEGORIES =================


CATEGORIES = [


    "Cow Milk",

    "Buffalo Milk",

    "Premium Milk"

]





# ================= STARTUP =================


create_default_products()


# ================= HOME =================


@app.route("/")
def home():


    products = get_all_products()


    return render_template(

        "index.html",

        products=products,

        categories=CATEGORIES

    )






# ================= PROFILE =================


@app.route("/profile")
def profile():


    return render_template(

        "profile.html"

    )







# ================= CART ADD =================


@app.route("/add-cart", methods=["POST"])
def add_cart():


    product_id = request.form.get(
        "product_id"
    )


    product = get_products_collection().find_one(
        {
            "_id": ObjectId(product_id)
        }
    )



    if not product:


        return jsonify({

            "status":"error",

            "message":"Product not found"

        })



    cart = session.get(

        "cart",

        []

    )



    found = False



    for item in cart:


        if item["id"] == product_id:


            item["qty"] += 1


            found = True

            break





    if not found:


        cart.append({

            "id":str(product["_id"]),

            "name":product["name"],

            "price":product["price"],

            "image":product["image"],

            "qty":1

        })





    session["cart"] = cart



    return jsonify({

        "status":"success",

        "message":"Added to cart"

    })







# ================= CART PAGE =================


@app.route("/cart")
def cart():


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







# ================= INCREASE QUANTITY =================


@app.route("/increase/<id>")
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







# ================= DECREASE QUANTITY =================


@app.route("/decrease/<id>")
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







# ================= REMOVE ITEM =================


@app.route("/remove/<id>")
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







# ================= CHECKOUT =================


@app.route("/checkout")
def checkout():


    cart = session.get(

        "cart",

        []

    )



    if not cart:


        return redirect("/")



    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )



    return render_template(

        "checkout.html",

        cart=cart,

        total=total

    )


# ================= PLACE ORDER =================


@app.route("/place-order", methods=["POST"])
def place_order():


    cart = session.get(

        "cart",

        []

    )


    if not cart:


        return redirect("/")




    name = request.form.get(
        "name"
    )


    phone = request.form.get(
        "phone"
    )


    address = request.form.get(
        "address"
    )




    if not phone or not phone.isdigit() or len(phone) != 10:


        total = sum(

            item["price"] * item["qty"]

            for item in cart

        )


        return render_template(

            "checkout.html",

            cart=cart,

            total=total,

            error="Enter valid 10 digit mobile number"

        )





    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )




    order = {


        "name":name,


        "phone":phone,


        "address":address,


        "products":cart,


        "total":total,


        "status":"Pending",


        "date":datetime.now()


    }





    get_orders_collection().insert_one(

        order

    )



    session.clear()



    return render_template(

        "success.html"

    )








# ================= ADMIN DASHBOARD =================


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


        session.permanent = True



        return redirect(

            "/admin"

        )





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


    return redirect(

        "/admin"

    )








# ================= UPDATE ORDER STATUS =================


@app.route("/update-status/<id>/<status>")
def update_status(id,status):


    allowed_status = [

        "Pending",

        "Delivered"

    ]



    if status not in allowed_status:


        return redirect(

            "/admin"

        )





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



    return redirect(

        "/admin"

    )








# ================= DELETE ORDER =================


@app.route("/delete-order/<id>")
def delete_order(id):


    get_orders_collection().delete_one(

        {

            "_id":ObjectId(id)

        }

    )


    return redirect(

        "/admin"

    )


# ================= ADMIN PRODUCT MANAGEMENT =================


@app.route("/admin-products")
def admin_products():


    if not session.get("admin"):


        return redirect("/admin")



    products = get_all_products()



    return render_template(

        "admin_products.html",

        products=products

    )








# ================= ADD PRODUCT =================


@app.route("/add-product", methods=["POST"])
def add_product():


    if not session.get("admin"):


        return redirect("/admin")



    name = request.form.get(
        "name"
    )


    price = request.form.get(
        "price"
    )


    image = request.form.get(
        "image"
    )


    description = request.form.get(
        "description"
    )



    product = {


        "name":name,


        "price":int(price),


        "image":image,


        "description":description


    }



    get_products_collection().insert_one(

        product

    )



    return redirect(

        "/admin-products"

    )








# ================= DELETE PRODUCT =================


@app.route("/delete-product/<id>")
def delete_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    get_products_collection().delete_one(

        {

            "_id":ObjectId(id)

        }

    )



    return redirect(

        "/admin-products"

    )








# ================= EDIT PRODUCT PAGE =================


@app.route("/edit-product/<id>")
def edit_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    product = get_products_collection().find_one(

        {

            "_id":ObjectId(id)

        }

    )



    return render_template(

        "edit_product.html",

        product=product

    )








# ================= UPDATE PRODUCT =================


@app.route("/update-product/<id>", methods=["POST"])
def update_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    name = request.form.get(
        "name"
    )


    price = request.form.get(
        "price"
    )


    image = request.form.get(
        "image"
    )


    description = request.form.get(
        "description"
    )



    get_products_collection().update_one(

        {

            "_id":ObjectId(id)

        },


        {

            "$set":{

                "name":name,

                "price":int(price),

                "image":image,

                "description":description

            }

        }

    )



    return redirect(

        "/admin-products"

        )


# ================= CART COUNT API =================


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








# ================= CLEAR CART =================


@app.route("/clear-cart")
def clear_cart():


    session.pop(

        "cart",

        None

    )


    return redirect("/")








# ================= DATABASE CHECK =================


@app.route("/database-check")
def database_check():


    try:


        get_orders_collection().find_one()



        return jsonify({

            "database":"connected"

        })



    except Exception as e:


        return jsonify({

            "database":"error",

            "message":str(e)

        })








# ================= HEALTH CHECK =================


@app.route("/health")
def health():


    return jsonify({

        "status":"KSR Dairy Foods is running",

        "time":datetime.now().strftime(

            "%d-%m-%Y %H:%M:%S"

        )

    })








# ================= SESSION SETTINGS =================


@app.before_request
def session_settings():


    session.permanent = True







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







# ================= START SERVER =================


if __name__ == "__main__":


    port = int(

        os.environ.get(

            "PORT",

            5000

        )

    )



    debug_mode = os.environ.get(

        "DEBUG",

        "False"

    ).lower() == "true"





    app.run(

        host="0.0.0.0",

        port=port,

        debug=debug_mode

            )

