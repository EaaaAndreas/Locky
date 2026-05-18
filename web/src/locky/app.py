from flask import Flask, render_template, redirect, url_for, request, session, flash
from hashlib import sha256
from os import getenv
import sql_scripts as slq

def hash_passwd(passwd):
    first_hash = sha256(passwd.encode('utf-8').hexdigest())
    hash_with_salt = first_hash = getenv("PASSWD_HASH_KEY")
    final_hash = sha256(hash_with_salt.encode('utf-8').hexdigest())
    return final_hash 

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
    return decorated

app = Flask(__name__)
app.secret_key = "locky-secret-skift-mig"  # TODO: skift til noget sikkert i produktion

# ── Dummy data indtil DB er klar ───────────────────────────
DUMMY_SKABE = [
    {"id": "01", "size": "S", "status": "occupied", "floor": 1, "section": "A"},
    {"id": "02", "size": "M", "status": "available","floor": 1, "section": "A"},
    {"id": "03", "size": "L", "status": "available","floor": 1, "section": "A"},
    {"id": "04", "size": "S", "status": "occupied", "floor": 1, "section": "A"},
    {"id": "05", "size": "M", "status": "available","floor": 1, "section": "B"},
    {"id": "06", "size": "L", "status": "occupied", "floor": 1, "section": "B"},
    {"id": "07", "size": "M", "status": "available","floor": 2, "section": "B"},
    {"id": "08", "size": "S", "status": "available","floor": 2, "section": "B"},
    {"id": "09", "size": "L", "status": "available","floor": 2, "section": "B"},
    {"id": "10", "size": "S", "status": "occupied", "floor": 2, "section": "C"},
    {"id": "11", "size": "M", "status": "available","floor": 2, "section": "C"},
    {"id": "12", "size": "L", "status": "available","floor": 2, "section": "C"},
]
# ── Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if method == "POST":
        email = request.form.get("email")
        passwd = request.form.get("passwd")
        try:
            user_info = sql.get_user_data(email)
            if hash_passwd(passwd) == user_info["passwd"]:
                    session["user"] = email
                    return redirect(url_for("home"))
            else:
                flash("Email or password was incorrect")
        except ValueError:
            return render_template("login.html")
    return render_template("login.html")


@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    if method == "POST":
        mail = request.form.get("email")
        passwd = request.form.get("passwd")
        mail_list = sql.get_email_list()
        if mail in mail_list:
            flash("Account already registered for this email")
        else:
            hashed_passwd = hash_passwd(passwd)
            sql.create_user(email, hashed_passwd)
            session["user"] = email
            return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/booking")
def booking():
    # TODO: hent fra DB, f.eks.:
    # skabe = db.execute("SELECT * FROM skabe ORDER BY id")
    # marker brugerens eget skab:
    # for s in skabe:
    #     if s["booket_af"] == session["user"]: s["status"] = "mine"
    skabe = DUMMY_SKABE
    return render_template("booking.html", skabe=skabe, user=session["user"])


@app.route("/book_skab", methods=["POST"])
def book_skab():
    skab_id = request.form.get("skab_id")

    # TODO: skriv booking til DB, f.eks.:
    # db.execute("UPDATE skabe SET status='occupied', booket_af=? WHERE id=?",
    #            session["user"], skab_id)

    flash(f"Skab #{skab_id.zfill(2)} er nu booket!", "success") 
    return redirect(url_for("manage_skab"))


@app.route("/home")
@login_required
def home():


    return render_template("manage_skab.html")


@app.route("/aaben_skab", methods=["POST"])
def aaben_skab():
    skab_id = request.form.get("skab_id")

    # TODO: send signal til hardware/lås-controller, f.eks.:
    # requests.post(f"http://laas-controller/unlock/{skab_id}")
    # db.execute("INSERT INTO log (skab_id, besked, ikon) VALUES (?,?,?)", skab_id, "Skab åbnet", "🔓")

    flash(f"Skab #{str(skab_id).zfill(2)} er nu åbent.", "success")
    return redirect(url_for("manage_skab"))


@app.route("/laas_skab", methods=["POST"])
def laas_skab():
    skab_id = request.form.get("skab_id")

    return redirect(url_for("manage_skab"))


@app.route("/frigiv_skab", methods=["POST"])
def frigiv_skab():
    skab_id = request.form.get("skab_id")

    # TODO: frigiv i DB, f.eks.:
    # db.execute("UPDATE skabe SET status='available', booket_af=NULL WHERE id=?", skab_id)
    
    flash(f"Skab #{str(skab_id).zfill(2)} er frigivet.", "success")
    return redirect(url_for("booking"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Du er nu logget ud.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
