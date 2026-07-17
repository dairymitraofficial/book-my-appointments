from flask import Blueprint, render_template, request, redirect, session, flash
import bcrypt
import os
import logging
from werkzeug.utils import secure_filename

from extensions import get_db, csrf
from utils.otp import create_otp, verify_otp
from utils.email import send_email

logger = logging.getLogger(__name__)

customer_auth_bp = Blueprint("customer_auth", __name__)

# ===============================
# CUSTOMER LOGIN
# ===============================
@customer_auth_bp.route("/customer/login", methods=["GET", "POST"])
@csrf.exempt
def customer_login():
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        if request.method == "POST":

            email = request.form.get("email")
            pwd = request.form.get("password")

            cur.execute("SELECT * FROM customers WHERE email=%s", (email,))
            u = cur.fetchone()

            if not u:
                flash("Email not registered.", "error")
                return redirect("/customer/login")

            if not bcrypt.checkpw(pwd.encode(), u["password_hash"].encode()):
                flash("Incorrect password.", "error")
                return redirect("/customer/login")

            # SESSION SET
             
            session.permanent = True  
            session["role"] = "customer"
            session["customer_id"] = u["id"]

            # PROFILE COMPLETENESS CHECK
            cur.execute("""
                SELECT full_name
                FROM customer_profiles
                WHERE customer_id=%s
            """, (u["id"],))
            profile = cur.fetchone()

            if not profile or not profile["full_name"]:
                return redirect("/customer/signup/profile")

            return redirect("/customer/account")

        return render_template("customer/auth/login.html")

    except Exception as e:
        logger.exception("Customer login failed")
        flash("Network issue.", "error")
        return redirect("/customer/login")


# ===============================
# SIGNUP – EMAIL
# ===============================
@customer_auth_bp.route("/customer/signup/email", methods=["GET", "POST"])
@csrf.exempt
def customer_signup_email():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":

        print("========== CUSTOMER SIGNUP ==========")

        email = request.form.get("email")
        print("Email:", email)

        cur.execute("SELECT id FROM customers WHERE email=%s", (email,))
        if cur.fetchone():
            print("User already exists")
            flash("User already exists. Please login.", "error")
            return redirect("/customer/signup/email")

        print("Creating OTP...")
        otp = create_otp(email, "customer")
        print("Generated OTP:", otp)

        print("Sending Email...")
        result = send_email(
            email,
            "Your OTP Verification Code",
            f"Your OTP is {otp}. It is valid for 2 minutes."
        )

        print("Email Result:", result)

        session["signup_email"] = email
        return redirect("/customer/signup/otp")

    return render_template("customer/auth/signup_email.html")


# ===============================
# SIGNUP – OTP
# ===============================
@customer_auth_bp.route("/customer/signup/otp", methods=["GET", "POST"])
@csrf.exempt
def customer_signup_otp():
    if request.method == "POST":
        if verify_otp(
            session.get("signup_email"),
            "customer",
            request.form.get("otp")
        ):
            return redirect("/customer/signup/password")

        flash("Invalid OTP.", "error")
        return redirect("/customer/signup/otp")

    return render_template("customer/auth/signup_otp.html")


# ===============================
# SIGNUP – PASSWORD
# ===============================
@customer_auth_bp.route("/customer/signup/password", methods=["GET", "POST"])
@csrf.exempt
def customer_signup_password():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        pwd = bcrypt.hashpw(
            request.form.get("password").encode(),
            bcrypt.gensalt()
        )

        # INSERT CUSTOMER
        cur.execute(
            "INSERT INTO customers (email, password_hash) VALUES (%s, %s)",
            (session["signup_email"], pwd.decode())
        )
        customer_id = cur.lastrowid

        # INSERT EMPTY PROFILE
        cur.execute(
            "INSERT INTO customer_profiles (customer_id, full_name, address) "
            "VALUES (%s, '', '')",
            (customer_id,)
        )

        db.commit()
        session.pop("signup_email", None)

        return redirect("/customer/login")

    return render_template("customer/auth/signup_password.html")


# ===============================
# SIGNUP – BASIC PROFILE INFO
# ===============================
@customer_auth_bp.route("/customer/signup/profile", methods=["GET", "POST"])
@csrf.exempt
def customer_signup_profile():
    if "customer_id" not in session:
        return redirect("/customer/login")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name")
        building = request.form.get("building")
        area = request.form.get("area")
        pincode = request.form.get("pincode")
        state = request.form.get("state")
        district = request.form.get("district")
        post_office = request.form.get("post_office")

        address = f"{building}, {area}, {district}, {state} - {pincode}"

        image_filename = None
        if "profile_photo" in request.files:
            img = request.files["profile_photo"]
            if img and img.filename:
                image_filename = secure_filename(img.filename)
                img.save(
                    os.path.join(
                        "static/uploads/customer_profiles",
                        image_filename
                    )
                )

        cur.execute("""
            UPDATE customer_profiles
            SET full_name=%s,
                building=%s,
                area=%s,
                post_office=%s,
                district=%s,
                state=%s,
                pincode=%s,
                address=%s,
                profile_photo=COALESCE(%s, profile_photo)
            WHERE customer_id=%s
        """, (
            full_name,
            building,
            area,
            post_office,
            district,
            state,
            pincode,
            address,
            image_filename,
            session["customer_id"]
        ))

        db.commit()
        flash("Profile completed.", "success")
        return redirect("/customer/categories")

    return render_template("customer/auth/signup_basic_info.html")
