from flask import Blueprint, render_template, redirect, session, request, jsonify
from extensions import get_db, csrf
from flask import request, redirect, flash, session
from utils.email import send_email
core_bp = Blueprint("core", __name__)

# ===============================
# BASIC ROUTES
# ===============================
@core_bp.route("/")
def home():
    return render_template("entry/role_select.html")

@core_bp.route("/select-role/<role>")
def select_role(role):
    return redirect(f"/{role}/login")

@core_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# SAVE PUSH TOKEN (FINAL, FIXED)
# ===============================
@core_bp.route("/save-push-token", methods=["POST"])
@csrf.exempt
def save_push_token():
    data = request.get_json(silent=True) or {}
    token = data.get("token")

    if not token:
        return {"error": "token missing"}, 400

    if "owner_id" in session:
        user_id = session["owner_id"]
        role = "owner"
    elif "customer_id" in session:
        user_id = session["customer_id"]
        role = "customer"
    else:
        return {"error": "unauthorized"}, 401

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO push_tokens (user_id, role, token)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE token = VALUES(token)
    """, (user_id, role, token))

    db.commit()
    return {"status": "saved"}

@core_bp.route("/about")
def about():
    return render_template("static_pages/about.html")

@core_bp.route("/learn")
def learn():
    return render_template("static_pages/learn.html")

@core_bp.route("/contact")
def contact():
    return render_template("static_pages/contact.html")

@core_bp.route("/rating")
def rating():
    return render_template("static_pages/rating.html")




@core_bp.route("/contact/send", methods=["POST"])
@csrf.exempt
def send_contact_message():

    # 🔐 Registered user email
    user_email = session.get("customer_email") or session.get("owner_email")

    if not user_email:
        flash("Please login to contact support.", "danger")
        return redirect("/contact")

    subject = request.form.get("subject")
    message = request.form.get("message")

    full_message = f"""
Message from registered user: {user_email}

---------------------------------
{message}
---------------------------------
"""

    try:
        send_email(
        to="dairymitr.official@gmail.com",
        subject=f"[BMA Contact] {subject}",
        body=full_message
)
        flash("Your message has been sent successfully.", "success")

    except Exception as e:
        print("EMAIL ERROR:", e)
        flash("Unable to send message. Please try again later.", "danger")

    return redirect("/contact")
