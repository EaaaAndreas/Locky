from flask import Flask, session, url_for, redirect, static, request, flash 
from hashlib import sha256
from os import getenv 

app = Flask(__name__)

def hash_passwd(passwd):
    first_hash = sha256(passwd.encode('utf-8').hexdigest())
    hash_with_salt = first_hash = getenv("PASSWD_HASH_KEY")
    final_hash = sha256(hash_with_salt.encode('utf-8').hexdigest())
    return final_hash 


@app.route("/", methods["POST","GET"])
def login():
    if method == "POST":
        email = request.form.get("email")
        passwd = request.form.get("passwd")
        try:
            user_info = select_query(email)
            if hash_passwd(passwd) == user_info["passwd"]:
                    redirect("home")
            else:
                flash("Email or password was incorrect")
        except ValueError:
            return render_template("login.html")
    return render_template("login.html")

@app.route("/register", methods["POST","GET"])
def register():
    if method == "POST":
        mail = request.form.get("email")
        passwd = request.form.get("passwd")
        mail_list = select_query 
        if mail in mail_list:
            flash("Account already registered for this email")
        else:
            hashed_passwd = hash_passwd(passwd)
            insert_query(email, hashed_passwd)
            redirect("home")

    return render_template("register.html")


        

@app.route("home")
def home():
    print("hello home")
        

if __name__ == '__main__':
    app.run()
