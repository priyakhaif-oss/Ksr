from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import os

from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from bson.errors import InvalidId
from authlib.integrations.flask_client import OAuth


load_dotenv()



# ==================================================
# APP CONFIG
# ==================================================

app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ksr_dairy_secret_key"
)




oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)




app.permanent_session_lifetime = timedelta(
    days=7
)





# ==================================================
# IMAGE UPLOAD CONFIG
# ==================================================

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







# ==================================================
# BRANDING
# ==================================================

SITE_NAME = "KSR Dairy Foods"

SITE_TAGLINE = "Fresh Milk Delivered To Your Doorstep"





@app.context_processor
def inject_brand():

    cart = session.get(
        "cart",
        []
    )

    cart_count = sum(
        item.get("qty", 0)
        for item in cart
    )

    return {

        "site_name": SITE_NAME,

        "site_tagline": SITE_TAGLINE,

        "cart_count": cart_count,

        "user_name": session.get("user_name"),

        "user_email": session.get("user_email"),

        "user_picture": session.get("user_picture"),

        "user_phone": session.get("user_phone"),
        
        "user_address": session.get("user_address"),

        "logged_in": bool(session.get("user_email"))

    }








# ==================================================
# ADMIN LOGIN
# ==================================================

ADMIN_USERNAME = "ksr"

ADMIN_PASSWORD = "123"







# ==================================================
# DATABASE
# ==================================================

mongo_uri = os.environ.get(
    "MONGO_URI"
)





def get_database():

    client = MongoClient(
        mongo_uri
    )

    return client["ksr_dairy"]





def get_orders_collection():

    return get_database()["orders"]





def get_products_collection():

    return get_database()["products"]



def get_users_collection():
    return get_database()["users"]






# ==================================================
# DEFAULT PRODUCTS
# ==================================================

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

        .sort(
            "_id",
            -1
        )

    )







# ==================================================
# CATEGORY LIST
# ==================================================

CATEGORIES = [

    "Cow Milk",

    "Buffalo Milk",

    "Premium Milk"

]







# ==================================================
# STARTUP
# ==================================================

create_default_products()


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():

    products = get_all_products()


    return render_template(
        "index.html",
        products=products,
        categories=CATEGORIES
    )



# ======================================================
# GOOGLE LOGIN
# ======================================================

@app.route("/login/google")
def login_google():

    # Save the page where user started Google login
    next_page = request.args.get("next")

    if next_page:
        session["login_next"] = next_page
    else:
        session.pop("login_next", None)

    return oauth.google.authorize_redirect(
        url_for(
            "google_callback",
            _external=True
        )
    )




# ==================================================
# PROFILE
# ==================================================




@app.route("/profile")
def profile():

    user = None

    if session.get("user_email"):

        user = get_users_collection().find_one(

            {

                "email": session["user_email"]

            }

        )

    return render_template(

        "profile.html",

        user=user

    )





# ==================================================
# GOOGLE CALLBACK
# ==================================================

@app.route("/auth/google/callback")
def google_callback():

    token = oauth.google.authorize_access_token()

    user_info = token.get("userinfo")

    if not user_info:
        return redirect("/profile")


    user = {

        "name": user_info["name"],

        "email": user_info["email"],

        "picture": user_info.get(
            "picture",
            ""
        )

    }


    # ==============================================
    # SAVE / UPDATE USER
    # ==============================================

    get_users_collection().update_one(

        {
            "email": user["email"]
        },

        {

            "$set": {

                "name": user["name"],

                "picture": user["picture"],

                "updated": datetime.now()

            },

            "$setOnInsert": {

                "email": user["email"],

                "phone": "",

                "address": "",

                "created": datetime.now()

            }

        },

        upsert=True

    )


    # ==============================================
    # CREATE LOGIN SESSION
    # ==============================================

    session["user_email"] = user["email"]

    session["user_name"] = user["name"]

    session["user_picture"] = user["picture"]


    saved_user = get_users_collection().find_one(

        {
            "email": user["email"]
        }

    )


    session["user_phone"] = saved_user.get(
        "phone",
        ""
    )


    session["user_address"] = saved_user.get(
        "address",
        ""
    )


    session.permanent = True


    # ==============================================
    # RETURN TO PREVIOUS PAGE
    # ==============================================

    next_page = session.pop(
        "login_next",
        None
    )


    if next_page:

        return redirect(next_page)


    # ==============================================
    # DEFAULT: PROFILE
    # ==============================================

    return redirect("/profile")








# ==================================================
# EDIT PROFILE
# ==================================================

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if not session.get("user_email"):
        return redirect("/profile")

    users = get_users_collection()

    user = users.find_one(
        {
            "email": session["user_email"]
        }
    )

    if not user:
        return redirect("/profile")

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        if phone:

            if not phone.isdigit() or len(phone) != 10:

                return render_template(
                    "edit_profile.html",
                    user=user,
                    error="Enter valid 10 digit mobile number"
                )

        users.update_one(

            {
                "email": session["user_email"]
            },

            {
                "$set": {

                    "name": name,

                    "phone": phone,

                    "address": address,

                    "updated": datetime.now()

                }
            }

        )

        session["user_name"] = name

        return redirect("/profile")

    return render_template(

        "edit_profile.html",

        user=user

    )





# ==================================================
# USER ORDERS
# ==================================================

@app.route("/orders")
def user_orders():

    if not session.get("user_email"):
        return redirect("/profile")

    email = session["user_email"]

    orders = list(
        get_orders_collection()
        .find({
            "user_email": email
        })
        .sort(
            "date",
            -1
        )
    )

    return render_template(
        "orders.html",
        orders=orders
    )





# ==================================================
# ADD TO CART
# ==================================================

@app.route("/add-cart", methods=["POST"])
def add_cart():


    product_id = request.form.get(
        "product_id"
    )



    try:

        product = get_products_collection().find_one(
            {
                "_id":ObjectId(product_id)
            }
        )


    except InvalidId:


        return jsonify({

            "status":"error",

            "message":"Invalid Product"

        })





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

            "message":"Out Of Stock"

        })







    cart = session.get(
        "cart",
        []
    )



    found = False



    for item in cart:



        if item["id"] == product_id:



            if item["qty"] >= stock:


                return jsonify({

                    "status":"limit",

                    "message":"Stock limit reached"

                })



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








# ==================================================
# CART PAGE
# ==================================================

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








# ==================================================
# INCREASE CART QUANTITY
# ==================================================

@app.route("/increase/<id>")
def increase(id):


    cart = session.get(
        "cart",
        []
    )



    try:

        product = get_products_collection().find_one(
            {
                "_id":ObjectId(id)
            }
        )


    except InvalidId:


        return redirect("/cart")





    for item in cart:



        if item["id"] == id:



            current_stock = product.get(
                "stock",
                0
            )


            if item["qty"] < current_stock:

                item["qty"] += 1


            break






    session["cart"] = cart



    return cart_page()








# ==================================================
# DECREASE CART QUANTITY
# ==================================================

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








# ==================================================
# REMOVE CART ITEM
# ==================================================

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



# ==================================================
# CHECKOUT PAGE
# ==================================================

@app.route("/checkout")
def checkout():

    # Login required
    if not session.get("user_email"):

        return redirect(
            url_for(
                "login_google",
                next="/checkout"
            )
        )


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



# ==================================================
# PLACE ORDER
# ==================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    # ==============================================
    # LOGIN REQUIRED
    # ==============================================

    if not session.get("user_email"):
        return redirect(
            url_for(
                "login_google",
                next="/checkout"
            )
        )


    cart = session.get(
        "cart",
        []
    )

    if not cart:

        return redirect("/")


    # ==============================================
    # GET DELIVERY DETAILS
    # ==============================================

    name = request.form.get(
        "name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()


    # ==============================================
    # VALIDATE PHONE
    # ==============================================

    if (
        not phone
        or
        not phone.isdigit()
        or
        len(phone) != 10
    ):

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


    # ==============================================
    # SAVE DELIVERY DETAILS
    # ==============================================

    get_users_collection().update_one(

        {
            "email": session["user_email"]
        },

        {
            "$set": {

                "phone": phone,

                "address": address,

                "updated": datetime.now()

            }
        }

    )


    session["user_phone"] = phone

    session["user_address"] = address


    # ==============================================
    # STOCK FINAL CHECK
    # ==============================================

    for item in cart:

        try:

            product = get_products_collection().find_one(

                {
                    "_id": ObjectId(item["id"])
                }

            )

        except InvalidId:

            return redirect("/cart")


        if not product:

            return redirect("/cart")


        if item["qty"] > product.get("stock", 0):

            total = sum(

                i["price"] * i["qty"]

                for i in cart

            )

            return render_template(

                "checkout.html",

                cart=cart,

                total=total,

                error=f"{item['name']} stock unavailable"

            )


    # ==============================================
    # CALCULATE TOTAL
    # ==============================================

    total = sum(

        item["price"] * item["qty"]

        for item in cart

    )


    # ==============================================
    # CREATE ORDER
    # ==============================================

    order = {

        "name": name,

        "phone": phone,

        "address": address,

        "products": cart,

        "total": total,

        "status": "Pending",

        "date": datetime.now(),

        "user_email": session["user_email"]

    }


    # ==============================================
    # REDUCE STOCK
    # ==============================================

    for item in cart:

        get_products_collection().update_one(

            {
                "_id": ObjectId(item["id"])
            },

            {
                "$inc": {
                    "stock": -item["qty"]
                }
            }

        )


    # ==============================================
    # SAVE ORDER
    # ==============================================

    get_orders_collection().insert_one(
        order
    )


    # ==============================================
    # CLEAR ONLY CART
    # ==============================================

    session.pop(
        "cart",
        None
    )


    # ==============================================
    # SUCCESS
    # ==============================================

    return render_template(
        "success.html"
    )






# ==================================================
# ADMIN DASHBOARD
# ==================================================

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

        o for o in orders

        if o.get("status") == "Pending"

    ])




    delivered_orders = len([

        o for o in orders

        if o.get("status") == "Delivered"

    ])





    total_products = len(products)





    out_of_stock = len([

        p for p in products

        if p.get("stock",0) <= 0

    ])





    low_stock = len([

        p for p in products

        if 0 < p.get("stock",0) <= 10

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

        low_stock=low_stock,

        total_revenue=total_revenue

    )








# ==================================================
# ADMIN LOGIN
# ==================================================

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


        return redirect("/admin")





    return render_template(

        "admin_login.html",

        error="Invalid Username or Password"

    )







# ==================================================
# ADMIN LOGOUT
# ==================================================

@app.route("/admin-logout")
def admin_logout():


    session.pop(
        "admin",
        None
    )


    return redirect("/admin")





# ==================================================
# USER LOGOUT
# ==================================================


@app.route("/logout")
def logout():

    session.pop(
        "user_email",
        None
    )

    session.pop(
        "user_name",
        None
    )

    session.pop(
        "user_picture",
        None
    )

    session.pop(
        "user_phone",
        None
    )

    session.pop(
        "user_address",
        None
    )

    return redirect("/profile")




# ==================================================
# ADD PRODUCT
# ==================================================

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


    category = request.form.get(
        "category",
        "Milk"
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

        "category":category,

        "created":datetime.now()

    }






    get_products_collection().insert_one(

        product

    )



    return redirect("/admin")








# ==================================================
# EDIT PRODUCT PAGE
# ==================================================

@app.route("/edit-product/<id>")
def edit_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    try:

        product = get_products_collection().find_one(

            {
                "_id":ObjectId(id)
            }

        )


    except InvalidId:


        return redirect("/admin")





    if not product:


        return redirect("/admin")





    return render_template(

        "edit_product.html",

        product=product

    )








# ==================================================
# UPDATE PRODUCT
# ==================================================

@app.route("/update-product/<id>", methods=["POST"])
def update_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    try:

        product_id = ObjectId(id)


    except InvalidId:


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


    category = request.form.get(
        "category"
    )



    get_products_collection().update_one(

        {
            "_id":product_id
        },


        {
            "$set":{

                "name":name,

                "price":int(price),

                "description":description,

                "category":category

            }

        }

    )



    return redirect("/admin")








# ==================================================
# UPDATE STOCK
# ==================================================

@app.route("/update-stock/<id>", methods=["POST"])
def update_stock(id):


    if not session.get("admin"):


        return redirect("/admin")



    try:

        product_id = ObjectId(id)


    except InvalidId:


        return redirect("/admin")





    stock = request.form.get(
        "stock"
    )



    if stock is None:


        return redirect("/admin")





    get_products_collection().update_one(

        {
            "_id":product_id
        },


        {

            "$set":{

                "stock":int(stock)

            }

        }

    )



    return redirect("/admin")








# ==================================================
# DELETE PRODUCT
# ==================================================

@app.route("/delete-product/<id>")
def delete_product(id):


    if not session.get("admin"):


        return redirect("/admin")



    try:

        product_id = ObjectId(id)


    except InvalidId:


        return redirect("/admin")





    get_products_collection().delete_one(

        {
            "_id":product_id
        }

    )


    return redirect("/admin")



# ==================================================
# UPDATE ORDER STATUS
# ==================================================

@app.route("/update-status/<id>/<status>")
def update_status(id, status):


    if not session.get("admin"):

        return redirect("/admin")



    if status not in [

        "Pending",

        "Delivered"

    ]:

        return redirect("/admin")



    try:

        order_id = ObjectId(id)


    except InvalidId:

        return redirect("/admin")





    get_orders_collection().update_one(

        {

            "_id":order_id

        },


        {

            "$set":{

                "status":status

            }

        }

    )



    return redirect("/admin")








# ==================================================
# DELETE ORDER + RESTORE STOCK
# ==================================================

@app.route("/delete-order/<id>")
def delete_order(id):


    if not session.get("admin"):

        return redirect("/admin")



    try:

        order_id = ObjectId(id)


    except InvalidId:

        return redirect("/admin")





    order = get_orders_collection().find_one(

        {

            "_id":order_id

        }

    )



    if order:


        # Restore product stock

        for item in order.get("products",[]):


            try:


                get_products_collection().update_one(

                    {

                        "_id":ObjectId(item["id"])

                    },


                    {

                        "$inc":{

                            "stock":item["qty"]

                        }

                    }

                )


            except:

                pass







        get_orders_collection().delete_one(

            {

                "_id":order_id

            }

        )



    return redirect("/admin")









# ==================================================
# ADMIN GRAPH DATA
# ==================================================

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







    monthly_orders = {


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



        date = order.get(
            "date"
        )



        if date:


            month = date.strftime("%b")



            if month in monthly_sales:


                monthly_sales[month] += order.get(

                    "total",

                    0

                )



                monthly_orders[month] += 1








    return jsonify({


        "labels":list(

            monthly_sales.keys()

        ),



        "sales":list(

            monthly_sales.values()

        ),



        "orders":list(

            monthly_orders.values()

        )



    })









# ==================================================
# PRODUCT STOCK STATUS API
# ==================================================

@app.route("/stock-status")
def stock_status():


    if not session.get("admin"):


        return jsonify({

            "error":"Unauthorized"

        }),403






    products = get_all_products()



    data = []



    for product in products:


        stock = product.get(

            "stock",

            0

        )



        if stock <= 0:


            status = "Out Of Stock"



        elif stock <= 10:


            status = "Low Stock"



        else:


            status = "In Stock"




        data.append({

            "name":product["name"],

            "stock":stock,

            "status":status

        })





    return jsonify(data)




# ==================================================
# CART COUNT API
# ==================================================

@app.route("/cart-count")
def cart_count():


    cart = session.get(

        "cart",

        []

    )


    count = sum(

        item.get("qty",0)

        for item in cart

    )


    return jsonify({

        "count":count

    })









# ==================================================
# CLEAR CART
# ==================================================

@app.route("/clear-cart")
def clear_cart():


    session.pop(

        "cart",

        None

    )


    return redirect("/")








# ==================================================
# DATABASE CHECK
# ==================================================

@app.route("/database-check")
def database_check():


    try:


        get_products_collection().find_one()

        get_orders_collection().find_one()



        return jsonify({

            "database":"connected"

        })




    except Exception as e:


        return jsonify({

            "database":"error",

            "message":str(e)

        })









# ==================================================
# HEALTH CHECK
# ==================================================

@app.route("/health")
def health():


    return jsonify({


        "status":

        "KSR Dairy Foods is running",



        "time":

        datetime.now().strftime(

            "%d-%m-%Y %H:%M:%S"

        )


    })









# ==================================================
# ERROR HANDLING
# ==================================================

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







# ==================================================
# SESSION SETTINGS
# ==================================================

@app.before_request
def session_settings():


    session.permanent = True







# ==================================================
# RUN SERVER
# ==================================================

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



