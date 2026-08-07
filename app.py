from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime, timedelta
import os

from werkzeug.utils import secure_filename
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





# ================= IMAGE UPLOAD =================

UPLOAD_FOLDER = "static/uploads"


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



if not os.path.exists(UPLOAD_FOLDER):

    os.makedirs(UPLOAD_FOLDER)




def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(".",1)[1].lower()

        in ALLOWED_EXTENSIONS

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








# ================= DEFAULT PRODUCTS =================


DEFAULT_PRODUCTS = [


    {


        "name":"Cow Milk",

        "price":60,

        "image":"/static/images/cow-milk.jpg",

        "description":"Fresh pure cow milk",

        "stock":50,

        "category":"Cow Milk"

    },


    {


        "name":"Buffalo Milk",

        "price":80,

        "image":"/static/images/buffalo-milk.jpg",

        "description":"Rich and creamy buffalo milk",

        "stock":50,

        "category":"Buffalo Milk"

    },


    {


        "name":"Premium Buffalo Milk",

        "price":90,

        "image":"/static/images/premium-milk.jpg",

        "description":"Premium quality buffalo milk",

        "stock":30,

        "category":"Premium Milk"

    }


]







def create_default_products():


    collection = get_products_collection()



    if collection.count_documents({}) == 0:


        collection.insert_many(
            DEFAULT_PRODUCTS
        )






def get_all_products():


    return list(

        get_products_collection()

        .find()

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







# ================= ADD CART =================


@app.route("/add-cart", methods=["POST"])
def add_cart():


    product_id = request.form.get(
        "product_id"
    )



    product = get_products_collection().find_one(

        {

            "_id":ObjectId(product_id)

        }

    )



    if not product:


        return jsonify({

            "status":"error",

            "message":"Product not found"

        })






    stock = product.get(

        "stock",

        0

    )



    if stock <= 0:


        return jsonify({

            "status":"out",

            "message":"Out of Stock"

        })







    cart = session.get(

        "cart",

        []

    )





    added = False





    for item in cart:


        if item["id"] == product_id:


            if item["qty"] < stock:


                item["qty"] += 1


                added = True


            else:


                return jsonify({

                    "status":"limit",

                    "message":"Stock limit reached"

                })


            break






    if not added:


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








# ================= CART =================


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








# ================= INCREASE =================


@app.route("/increase/<id>")
def increase(id):


    cart = session.get(

        "cart",

        []

    )



    product = get_products_collection().find_one(

        {

            "_id":ObjectId(id)

        }

    )



    for item in cart:


        if item["id"] == id:


            if product and item["qty"] < product.get("stock",0):


                item["qty"] += 1


            break





    session["cart"] = cart



    return cart_page()







# ================= DECREASE =================


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







# ================= REMOVE =================


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







    # ===== FINAL STOCK CHECK =====


    for item in cart:


        product = get_products_collection().find_one(

            {

                "_id":ObjectId(item["id"])

            }

        )


        if not product:


            return redirect("/cart")




        if item["qty"] > product.get("stock",0):


            return render_template(

                "checkout.html",

                cart=cart,

                total=sum(

                    i["price"] * i["qty"]

                    for i in cart

                ),

                error=f"{item['name']} stock not available"

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







    # ===== REDUCE STOCK =====


    for item in cart:


        get_products_collection().update_one(

            {

                "_id":ObjectId(item["id"])

            },


            {

                "$inc":{

                    "stock": -item["qty"]

                }

            }

        )







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




    products = get_all_products()






    total_orders = len(orders)




    pending_orders = len([

        o

        for o in orders

        if o.get("status") == "Pending"

    ])





    delivered_orders = len([

        o

        for o in orders

        if o.get("status") == "Delivered"

    ])





    total_products = len(products)





    out_of_stock = len([

        p

        for p in products

        if p.get("stock",0) <= 0

    ])





    total_revenue = sum(

        o.get("total",0)

        for o in orders

        if o.get("status")=="Delivered"

    )





    return render_template(

        "admin.html",

        orders=orders,

        products=products,

        total_orders=total_orders,

        pending_orders=pending_orders,

        delivered_orders=delivered_orders,

        total_products=total_products,

        out_of_stock=out_of_stock,

        total_revenue=total_revenue

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


    if status not in [

        "Pending",

        "Delivered"

    ]:


        return redirect("/admin")




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


    description = request.form.get(

        "description"

    )


    stock = request.form.get(

        "stock"

    )



    image = request.files.get(

        "image"

    )



    image_path = "/static/images/default.png"





    if image and allowed_file(image.filename):


        filename = secure_filename(

            image.filename

        )


        image.save(

            os.path.join(

                app.config["UPLOAD_FOLDER"],

                filename

            )

        )


        image_path = "/static/uploads/" + filename







    product = {


        "name":name,


        "price":int(price),


        "description":description,


        "image":image_path,


        "stock":int(stock),


        "category":"Milk"

    }





    get_products_collection().insert_one(

        product

    )



    return redirect("/admin")








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



    return redirect("/admin")








# ================= UPDATE STOCK =================


@app.route("/update-stock/<id>", methods=["POST"])
def update_stock(id):


    if not session.get("admin"):


        return redirect("/admin")



    stock = request.form.get(

        "stock"

    )



    get_products_collection().update_one(

        {

            "_id":ObjectId(id)

        },


        {

            "$set":{

                "stock":int(stock)

            }

        }

    )



    return redirect("/admin")



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







# ================= ADMIN GRAPH DATA =================


@app.route("/admin-chart-data")
def admin_chart_data():


    if not session.get("admin"):


        return jsonify({

            "error":"Unauthorized"

        }),403





    orders = list(

        get_orders_collection()

        .find()

    )





    monthly_sales = {

        "Jan":0,

        "Feb":0,

        "Mar":0,

        "Apr":0,

        "May":0,

        "Jun":0,

        "Jul":0,

        "Aug":0,

        "Sep":0,

        "Oct":0,

        "Nov":0,

        "Dec":0

    }






    for order in orders:


        date = order.get("date")


        if date:


            month = date.strftime("%b")


            if month in monthly_sales:


                monthly_sales[month] += order.get(

                    "total",

                    0

                )





    return jsonify({

        "labels":list(monthly_sales.keys()),

        "values":list(monthly_sales.values())

    })








# ================= DATABASE CHECK =================


@app.route("/database-check")
def database_check():


    try:


        get_orders_collection().find_one()


        get_products_collection().find_one()



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
def session_settings():


    session.permanent = True







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

