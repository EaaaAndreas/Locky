from flask import Flask, render_template, redirect, url_for, request, session, flash

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

# ── Helper ─────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("booking"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # TODO: erstat med rigtig DB-query, f.eks.:
        # user = db.execute("SELECT * FROM brugere WHERE username = ?", username)
        # if user and check_password_hash(user.password, password):

        if username and password:  # placeholder-validering
            session["user"] = username
            flash(f"Velkommen, {username}!", "success")
            return redirect(url_for("booking"))
        else:
            flash("Forkert brugernavn eller adgangskode.", "error")

    return render_template("login.html")


@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    if "user" in session:
        return redirect(url_for("booking"))

    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        password  = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        fornavn   = request.form.get("fornavn", "").strip()
        efternavn = request.form.get("efternavn", "").strip()

        if password != password2:
            flash("Adgangskoderne matcher ikke.", "error")
            return render_template("registrer.html")

        # TODO: gem i DB, f.eks.:
        # db.execute("INSERT INTO brugere (username, password, fornavn, efternavn) VALUES (?,?,?,?)",
        #            username, generate_password_hash(password), fornavn, efternavn)

        session["user"] = username
        flash(f"Konto oprettet! Velkommen, {fornavn}!", "success")
        return redirect(url_for("booking"))  # auto-redirect efter registrering

    return render_template("registrer.html")


@app.route("/booking")
@login_required
def booking():
    # TODO: hent fra DB, f.eks.:
    # skabe = db.execute("SELECT * FROM skabe ORDER BY id")
    # marker brugerens eget skab:
    # for s in skabe:
    #     if s["booket_af"] == session["user"]: s["status"] = "mine"
    skabe = DUMMY_SKABE
    return render_template("booking.html", skabe=skabe, user=session["user"])


@app.route("/book_skab", methods=["POST"])
@login_required
def book_skab():
    skab_id = request.form.get("skab_id")

    # TODO: skriv booking til DB, f.eks.:
    # db.execute("UPDATE skabe SET status='occupied', booket_af=? WHERE id=?",
    #            session["user"], skab_id)

    flash(f"Skab #{skab_id.zfill(2)} er nu booket!", "success")
    return redirect(url_for("manage_skab"))


@app.route("/manage_skab")
@login_required
def manage_skab():
    # TODO: hent brugerens skab fra DB, f.eks.:
    # skab = db.execute("SELECT * FROM skabe WHERE booket_af = ?", session["user"]).fetchone()
    # logs = db.execute("SELECT * FROM log WHERE skab_id = ? ORDER BY tid DESC LIMIT 10", skab["id"])

    # Dummy: vis skab #07 som eksempel
    skab = {"id": "07", "size": "Medium", "floor": 2, "section": "B", "booket_tid": "I dag 08:32"}
    logs = [
        {"ikon": "🔒", "besked": "Skab låst",        "tid": "I dag 10:14"},
        {"ikon": "🔓", "besked": "Skab åbnet",        "tid": "I dag 10:13"},
        {"ikon": "📦", "besked": "Booking oprettet",  "tid": "I dag 08:32"},
    ]
    return render_template("manage_skab.html", skab=skab, logs=logs, user=session["user"])


@app.route("/aaben_skab", methods=["POST"])
@login_required
def aaben_skab():
    skab_id = request.form.get("skab_id")

    # TODO: send signal til hardware/lås-controller, f.eks.:
    # requests.post(f"http://laas-controller/unlock/{skab_id}")
    # db.execute("INSERT INTO log (skab_id, besked, ikon) VALUES (?,?,?)", skab_id, "Skab åbnet", "🔓")

    flash(f"Skab #{str(skab_id).zfill(2)} er nu åbent.", "success")
    return redirect(url_for("manage_skab"))


@app.route("/laas_skab", methods=["POST"])
@login_required
def laas_skab():
    skab_id = request.form.get("skab_id")

    # TODO: send lås-signal til hardware, f.eks.:
    # requests.post(f"http://laas-controller/lock/{skab_id}")
    # db.execute("INSERT INTO log (skab_id, besked, ikon) VALUES (?,?,?)", skab_id, "Skab låst", "🔒")

    flash(f"Skab #{str(skab_id).zfill(2)} er nu låst.", "success")
    return redirect(url_for("manage_skab"))


@app.route("/frigiv_skab", methods=["POST"])
@login_required
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
