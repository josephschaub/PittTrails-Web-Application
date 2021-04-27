from flask import Flask, render_template, request, url_for, redirect, session
from flask_bootstrap import Bootstrap
from errors import bp as errors_bp
from google.cloud import datastore
import json

from user import UserStore, generate_credentials, hash_password
app = Flask(__name__)
app.secret_key = "hello"
bootstrap = Bootstrap(app)
app.register_blueprint(errors_bp)

datastore = datastore.Client()
userstore = UserStore(datastore)

@app.route("/home")
def home():
    if "user" in session:
        user = session["user"]
        return render_template("home.html")
    else:
        return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/trails")  
def trails():
    """ loads map_page.html """
    return render_template("map_page.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
  form = SearchForm()
  if not form.validate_on_submit():
    return redirect(url_for('home'))
  return redirect((url_for('search_results', query=form.search.data)))

@app.route('/', methods=["POST","GET"])
def login():
    session.permanent = False
    if request.method == "POST":
        user_email = request.form['email']
        password = request.form['password']
        user = userstore.verify_pass(user_email, password)
        if not user:
            return render_template("loginWrongPass.html", error="Incorrect password")
        session["user"] = user_email
        return redirect(url_for("home"))
    else:
        if "user" in session:
            return redirect(url_for("home"))
        return render_template("login.html")

@app.route("/create", methods=["POST","GET"])
def create():
    if request.method == "GET":
        user = get_user()
        if user:
            return redirect(url_for("home"))
        return render_template("create.html")
    else:    
        user = request.form.get("email")
        password = request.form.get("password")
        if user in userstore.list_existing_users():
            return render_template("createEmailTaken.html", error="A user with that email already exists")
        userstore.store_new_credentials(generate_credentials(user, password))
        session["user"] = user
        return redirect(url_for("home"))

@app.route("/profile",methods=["POST","GET"])
def profile():
    user = get_user()
    found_user = userstore.get_profile(user)
    name = found_user["name"]
    bio = found_user["bio"]
    pro_pic = found_user["pro_pic"]
    return render_template("profile.html",userinfo=user,name=name,bio=bio,pro_pic=pro_pic)

@app.route("/update_info", methods = ["POST","GET"])
def update_info():
    if request.method == "POST":    
        user = get_user()
        found_user = userstore.get_profile(user)
        name = request.form.get("fullname")
        bio = request.form.get("fullbio")
        pro_pic = found_user["pro_pic"]
        userstore.update_profile(user, name, bio, pro_pic)
        return redirect(url_for("profile"))
    else:
        return render_template("updateinfo.html")

@app.route("/pic_update", methods = ["POST","GET"])
def pic_update():
    if request.method == "POST":
        user = get_user()
        found_user = userstore.get_profile(user)
        name = found_user["name"]
        bio = found_user["bio"]
        pro_pic = request.form.get("choice")
        userstore.update_profile(user, name, bio, pro_pic)
        return redirect(url_for("profile"))
    else:
        return render_template("pic_update.html")        

def get_user():
    return session.get("user", None)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True) 
