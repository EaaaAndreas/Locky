from flask import Flask, render_template, redirect, url_for, request, session, flash
from argon2 import PasswordHasher
from os import getenv
import paho.mqtt.publish as mqtt_publish
import ssl
import sql_scripts as slq
from database import init_db
from generate_token import generate_jwt_token, verify_jwt_token


ph = PasswordHasher()
def hash_passwd(passwd):
    hashed_password = ph.hash(passwd)
    return hashed_password

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)
app.secret_key = getenv("FLASK_SECRET_KEY", "skift-mig")
app.jinja_env.filters["zfill"] = lambda s, n: str(s).zfill(n)

init_db()

# ── Dummy data indtil DB er klar ───────────────────────────
DUMMY_SKABE = [
    {"id": "01", "status": "available"},
    {"id": "02", "status": "available"},
    {"id": "03", "status": "available"},
    {"id": "04", "status": "available"},
    {"id": "05", "status": "available"},
]
# ── Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("username")
        passwd = request.form.get("password")
        user_info = slq.get_user_data(email)
        if not user_info:
            flash("Email or password was incorrect")
            return render_template("login.html")
        try:
            if ph.verify(user_info["passwd"], passwd):
                session["user"] = email
                access = slq.get_user_access(email)
                if access:
                    session["access_token"] = generate_jwt_token(email=email, locker_nr=access["locker_nr"])
                return redirect(url_for("booking"))
        except Exception:
            flash("Email or password was incorrect")
    return render_template("login.html")


@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    if request.method == "POST":
        mail = request.form.get("username")
        passwd = request.form.get("password")
        mail_list = slq.check_email_list()
        if mail in mail_list:
            flash("Account already registered for this email")
        else:
            hashed_passwd = hash_passwd(passwd)
            slq.create_user(mail, hashed_passwd)
            session["user"] = mail
            return redirect(url_for("booking"))
    return render_template("registrer.html")


@app.route("/booking")
@login_required
def booking():
    # TODO: hent fra DB, f.eks.:
    access = slq.get_user_access(session.get("user"))
    booked = slq.get_all_booked_lockers()
    skabe = [s.copy() for s in DUMMY_SKABE]
    for s in skabe:
        if access and s["id"] == access["locker_nr"]:
            s["status"] = "mine"
        elif s["id"] in booked:
            s["status"] = "booked"
    return render_template("booking.html", skabe=skabe, user=session["user"])


@app.route("/book_skab", methods=["POST"])
@login_required
def book_skab():
    skab_id = request.form.get("skab_id")
    if slq.get_user_access(session["user"]):
        flash("Du har allerede et booket skab.", "error")
        return redirect(url_for("booking"))
    if slq.get_locker_access(skab_id):
        flash(f"Skab #{skab_id.zfill(2)} er allerede booket.", "error")
        return redirect(url_for("booking"))
    slq.insert_into_access(skab_id, session["user"])
    session["access_token"] = generate_jwt_token(email=session["user"], locker_nr=skab_id)
    flash(f"Skab #{skab_id.zfill(2)} er nu booket!", "success")
    return redirect(url_for("manage_skab"))


@app.route("/manage_skab")
@login_required
def manage_skab():
    access = slq.get_user_access(session["user"])
    skab = None
    if access:
        for s in DUMMY_SKABE:
            if s["id"] == access["locker_nr"]:
                skab = s
                break
    return render_template("manage_skab.html", user=session["user"], skab=skab)


@app.route("/aaben_skab", methods=["POST"])
@login_required
def aaben_skab():
    skab_id = request.form.get("skab_id")

    payload = verify_jwt_token(session.get("access_token"))
    if not payload or payload.get("locker_nr") != skab_id:
        flash("Ugyldig eller udløbet adgangstilladelse.", "error")
        return ("Forbidden", 403)

    mqtt_publish.single(
        topic=f"locker/locker_nr{skab_id}/open",
        payload="open",
        hostname=getenv("MQTT_HOST", "mosquitto"),
        port=int(getenv("MQTT_PORT", 8883)),
        auth={"username": getenv("MQTT_SERVER_USER", "server"),
              "password": getenv("MQTT_SERVER_PASS", "server123")},
        tls={"ca_certs": "/certs/ca.crt", "tls_version": ssl.PROTOCOL_TLS,
             "cert_reqs": ssl.CERT_NONE},
    )

    flash(f"Skab #{str(skab_id).zfill(2)} er nu åbent.", "success")
    return redirect(url_for("manage_skab"))


@app.route("/laas_skab", methods=["POST"])
@login_required
def laas_skab():
    skab_id = request.form.get("skab_id")
    mqtt_publish.single(
        topic=f"locker/locker_nr{skab_id}/open",
        payload="lock",
        hostname=getenv("MQTT_HOST", "mosquitto"),
        port=int(getenv("MQTT_PORT", 8883)),
        auth={"username": getenv("MQTT_SERVER_USER", "server"),
              "password": getenv("MQTT_SERVER_PASS", "server123")},
        tls={"ca_certs": "/certs/ca.crt", "tls_version": ssl.PROTOCOL_TLS,
             "cert_reqs": ssl.CERT_NONE},
    )
    return ("", 204)


@app.route("/frigiv_skab", methods=["POST"])
@login_required
def frigiv_skab():
    skab_id = request.form.get("skab_id")
    slq.release_locker(skab_id)
    flash(f"Skab #{str(skab_id).zfill(2)} er frigivet.", "success")
    return redirect(url_for("booking"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Du er nu logget ud.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
