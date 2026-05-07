from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import joblib, os, geoip2.database
from db import get_db, init_db
from config import MODEL_PATH, VECTORIZER_PATH, ALLOWED_ATTACKS, ATTACK_INFO
import pyotp
import qrcode
from io import BytesIO
import base64

# ---------------- APP INIT ----------------
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

app.secret_key = "safenet_secret"
init_db()


# ---------------- LOGIN ----------------
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    db.close()
    return User(row[0], row[1]) if row else None

# ---------------- GEOIP ----------------
country_reader = geoip2.database.Reader("geoip/GeoLite2-Country.mmdb")
asn_reader = geoip2.database.Reader("geoip/GeoLite2-ASN.mmdb")

def geo(ip):
    if ip == "127.0.0.1":
        return "India", "Localhost"
    try:
        return (
            country_reader.country(ip).country.name,
            asn_reader.asn(ip).autonomous_system_organization
        )
    except:
        return "Unknown", "Unknown"

# ---------------- MODEL ----------------
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
vectorizer = joblib.load(VECTORIZER_PATH) if os.path.exists(VECTORIZER_PATH) else None

# ---------------- LOGGING ----------------
def log_query(q, label):
    ip = request.remote_addr
    country, org = geo(ip)
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO logs (time, query, label, source_ip, country, organization)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), q, label, ip, country, org))
    db.commit()
    db.close()

# ---------------- STATS ----------------
def stats():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM logs WHERE label=0")
    safe = cur.fetchone()[0]
    db.close()
    return total, safe, total - safe

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return redirect("/login")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            SELECT id, password, mfa_enabled, mfa_secret
            FROM users WHERE username=?
        """, (username,))
        row = cur.fetchone()
        db.close()

        if not row or row[1] != password:
            flash("Invalid credentials")
            return render_template("login.html")

        user_id, _, mfa_enabled, _ = row

        if mfa_enabled:
            session["mfa_user"] = user_id
            return redirect("/mfa")

        login_user(User(user_id, username))
        return redirect("/dashboard")

    return render_template("login.html")

# ---------- MFA SETUP ----------
@app.route("/mfa_setup")
@login_required
def mfa_setup():
    secret = pyotp.random_base32()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.username,
        issuer_name="SafeNet SOC"
    )

    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE users SET mfa_secret=? WHERE id=?",
        (secret, current_user.id)
    )
    db.commit()
    db.close()

    return render_template("mfa_setup.html", qr=qr_b64)

# ---------- MFA VERIFY ----------
@app.route("/mfa", methods=["GET", "POST"])
def mfa():
    user_id = session.get("mfa_user")
    if not user_id:
        return redirect("/login")

    if request.method == "POST":
        otp = request.form["otp"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT mfa_secret FROM users WHERE id=?", (user_id,))
        secret = cur.fetchone()[0]
        db.close()

        totp = pyotp.TOTP(secret)
        if totp.verify(otp):
            db = get_db()
            cur = db.cursor()
            cur.execute("UPDATE users SET mfa_enabled=1 WHERE id=?", (user_id,))
            db.commit()
            db.close()

            login_user(User(user_id, "admin"))
            session.pop("mfa_user")
            return redirect("/dashboard")

        flash("Invalid OTP")

    return render_template("mfa.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = attack_type = explanation = importance = None
    total, safe, attacks = stats()

    if request.method == "POST" and model and vectorizer:
        q = request.form["query"]
        pred = int(model.predict(vectorizer.transform([q]))[0])
        log_query(q, pred)
        attack_type = ALLOWED_ATTACKS.get(pred, "Unknown")
        result = "Malicious" if pred else "Safe"

        if result == "Malicious" and attack_type in ATTACK_INFO:
            explanation = ATTACK_INFO[attack_type]["what"]
            importance = ATTACK_INFO[attack_type]["why"]

    return render_template(
        "dashboard.html",
        total=total,
        safe=safe,
        attacks=attacks,
        result=result,
        attack_type=attack_type,
        explanation=explanation,
        importance=importance
    )

# ---------- MONITOR ----------
@app.route("/monitor_data")
@login_required
def monitor_data():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT time, query, label, source_ip, country, organization
        FROM logs ORDER BY id DESC LIMIT 50
    """)
    rows = cur.fetchall()
    db.close()

    return jsonify({
        "logs": [{
            "time": r[0],
            "query": r[1],
            "label": r[2],
            "ip": r[3],
            "country": r[4],
            "org": r[5]
        } for r in rows]
    })

@app.route("/monitor_stats")
@login_required
def monitor_stats():
    t, s, a = stats()
    return {"total": t, "benign": s, "malicious": a}

# ---------- ANALYTICS ----------
@app.route("/api/top_countries")
@login_required
def top_countries():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT country, COUNT(*) FROM logs
        WHERE label != 0
        GROUP BY country
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    db.close()
    return {
        "labels": [r[0] for r in rows],
        "counts": [r[1] for r in rows]
    }

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
