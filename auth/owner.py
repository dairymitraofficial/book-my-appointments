from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
from extensions import get_db, csrf
from utils.otp import create_otp, verify_otp
import bcrypt
import logging
import os

logger = logging.getLogger(__name__)

owner_auth_bp = Blueprint("owner_auth", __name__)

# ===============================
# UPLOAD CONFIG (FIXED)
# ===============================
UPLOAD_FOLDER = "static/uploads/owner_profiles"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===============================
# OWNER LOGIN
# ===============================
@owner_auth_bp.route("/owner/login", methods=["GET", "POST"])
@csrf.exempt
def owner_login():
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        if request.method == "POST":
            email = request.form["email"]
            pwd = request.form["password"]

            cur.execute("SELECT * FROM owners WHERE email=%s", (email,))
            owner = cur.fetchone()

            if not owner:
                flash("Email not registered.", "error")
                return redirect("/owner/login")

            if not bcrypt.checkpw(pwd.encode(), owner["password_hash"].encode()):
                flash("Incorrect password.", "error")
                return redirect("/owner/login")
               
            
            session.permanent = True
            session["role"] = "owner"
            session["owner_id"] = owner["id"]

            # PROFILE COMPLETENESS CHECK
            cur.execute(
                "SELECT business_name FROM owner_profiles WHERE owner_id=%s",
                (owner["id"],)
            )
            profile = cur.fetchone()

            if not profile or not profile["business_name"]:
                return redirect("/owner/signup/profile")

            return redirect("/owner/account")

        return render_template("owner/auth/login.html")

    except Exception:
        logger.exception("Owner login failed")
        flash("Network issue.", "error")
        return redirect("/owner/login")


# ===============================
# OWNER SIGNUP – EMAIL
# ===============================
@owner_auth_bp.route("/owner/signup/email", methods=["GET", "POST"])
@csrf.exempt
def owner_signup_email():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        email = request.form["email"]

        cur.execute("SELECT id FROM owners WHERE email=%s", (email,))
        if cur.fetchone():
            flash("User already exists. Please login.", "error")
            return redirect("/owner/signup/email")

        otp = create_otp(email, "owner")

        from utils.email import send_email
        send_email(
            email,
            "Your OTP Verification Code",
            f"Your OTP is {otp}. It is valid for 2 minutes."
        )

        session["signup_email"] = email
        return redirect("/owner/signup/otp")

    return render_template("owner/auth/signup_email.html")


# ===============================
# OWNER SIGNUP – OTP
# ===============================
@owner_auth_bp.route("/owner/signup/otp", methods=["GET", "POST"])
@csrf.exempt
def owner_signup_otp():
    if request.method == "POST":
        if verify_otp(
            session.get("signup_email"),
            "owner",
            request.form["otp"]
        ):
            return redirect("/owner/signup/password")

        flash("Invalid OTP.", "error")
        return redirect("/owner/signup/otp")

    return render_template("owner/auth/signup_otp.html")


# ===============================
# OWNER SIGNUP – PASSWORD
# ===============================
@owner_auth_bp.route("/owner/signup/password", methods=["GET", "POST"])
@csrf.exempt
def owner_signup_password():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        pwd_hash = bcrypt.hashpw(
            request.form["password"].encode(),
            bcrypt.gensalt()
        )

        cur.execute(
            "INSERT INTO owners (email, password_hash) VALUES (%s,%s)",
            (session["signup_email"], pwd_hash.decode())
        )
        owner_id = cur.lastrowid

        # EMPTY PROFILE ROW
        cur.execute(
            "INSERT INTO owner_profiles (owner_id, full_name, business_name, address) "
            "VALUES (%s,'','','')",
            (owner_id,)
        )

        db.commit()
        session.pop("signup_email", None)

        return redirect("/owner/login")

    return render_template("owner/auth/signup_password.html")


# ===============================
# OWNER SIGNUP – PROFILE
# ===============================
@owner_auth_bp.route("/owner/signup/profile", methods=["GET", "POST"])
@csrf.exempt
def owner_signup_profile():
    if "owner_id" not in session:
        return redirect("/owner/login")

    db = get_db()
    cur = db.cursor(dictionary=True)
    owner_id = session["owner_id"]

    if request.method == "POST":
        full_name = request.form["full_name"]
        business_name = request.form["business_name"]
        category_id = request.form["category_id"]
        custom_category = request.form.get("custom_category")

        building = request.form["building"]
        area = request.form["area"]
        pincode = request.form["pincode"]
        state = request.form["state"]
        district = request.form["district"]
        post_office = request.form["post_office"]

        description = request.form.get("description")
        address = f"{building}, {area}, {district}, {state} - {pincode}"

        image_filename = None
        if "profile_photo" in request.files:
            img = request.files["profile_photo"]
            if img and img.filename:
                image_filename = secure_filename(img.filename)
                img.save(os.path.join(UPLOAD_FOLDER, image_filename))

        # SAVE PROFILE
        cur.execute("""
            INSERT INTO owner_profiles (
                owner_id, full_name, business_name,
                building, area, post_office,
                district, state, pincode,
                address, description, profile_photo
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                full_name=VALUES(full_name),
                business_name=VALUES(business_name),
                building=VALUES(building),
                area=VALUES(area),
                post_office=VALUES(post_office),
                district=VALUES(district),
                state=VALUES(state),
                pincode=VALUES(pincode),
                address=VALUES(address),
                description=VALUES(description),
                profile_photo=COALESCE(VALUES(profile_photo), profile_photo)
        """, (
            owner_id, full_name, business_name,
            building, area, post_office,
            district, state, pincode,
            address, description, image_filename
        ))

        # CATEGORY
        cur.execute("DELETE FROM owner_categories WHERE owner_id=%s", (owner_id,))

        if category_id == "other" and custom_category:
            cur.execute("INSERT INTO categories (name) VALUES (%s)", (custom_category,))
            category_id = cur.lastrowid

        cur.execute(
            "INSERT INTO owner_categories (owner_id, category_id) VALUES (%s,%s)",
            (owner_id, category_id)
        )

        db.commit()
        return redirect("/owner/dashboard")  # ✅ FIXED

    # LOAD DATA (GET)
    cur.execute("SELECT * FROM owner_profiles WHERE owner_id=%s", (owner_id,))
    profile = cur.fetchone()

    cur.execute("SELECT category_id FROM owner_categories WHERE owner_id=%s", (owner_id,))
    cat = cur.fetchone()
    if profile and cat:
        profile["category_id"] = cat["category_id"]

    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()

    return render_template(
        "owner/auth/signup_basic_info.html",
        profile=profile,
        categories=categories
    )


# ===============================
# OWNER PROFILE EDIT
# ===============================
@owner_auth_bp.route("/owner/profile/edit", methods=["GET", "POST"])
@csrf.exempt
def edit_owner_profile():
    if "owner_id" not in session:
        return redirect("/owner/login")

    db = get_db()
    cur = db.cursor(dictionary=True)
    owner_id = session["owner_id"]

    if request.method == "POST":
        full_name = request.form["full_name"]
        business_name = request.form["business_name"]
        category_id = request.form["category_id"]
        custom_category = request.form.get("custom_category")

        building = request.form["building"]
        area = request.form["area"]
        pincode = request.form["pincode"]
        state = request.form["state"]
        district = request.form["district"]
        post_office = request.form["post_office"]

        description = request.form.get("description")
        address = f"{building}, {area}, {district}, {state} - {pincode}"

        image_filename = None
        if "profile_photo" in request.files:
            img = request.files["profile_photo"]
            if img and img.filename:
                image_filename = secure_filename(img.filename)
                img.save(os.path.join(UPLOAD_FOLDER, image_filename))

        cur.execute("""
            INSERT INTO owner_profiles (
                owner_id, full_name, business_name,
                building, area, post_office,
                district, state, pincode,
                address, description, profile_photo
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                full_name=VALUES(full_name),
                business_name=VALUES(business_name),
                building=VALUES(building),
                area=VALUES(area),
                post_office=VALUES(post_office),
                district=VALUES(district),
                state=VALUES(state),
                pincode=VALUES(pincode),
                address=VALUES(address),
                description=VALUES(description),
                profile_photo=COALESCE(VALUES(profile_photo), profile_photo)
        """, (
            owner_id, full_name, business_name,
            building, area, post_office,
            district, state, pincode,
            address, description, image_filename
        ))

        cur.execute("DELETE FROM owner_categories WHERE owner_id=%s", (owner_id,))

        if category_id == "other" and custom_category:
            cur.execute("INSERT INTO categories (name) VALUES (%s)", (custom_category,))
            category_id = cur.lastrowid

        cur.execute(
            "INSERT INTO owner_categories (owner_id, category_id) VALUES (%s,%s)",
            (owner_id, category_id)
        )

        db.commit()
        return redirect("/owner/dashboard")  # ✅ FIXED

    cur.execute("SELECT * FROM owner_profiles WHERE owner_id=%s", (owner_id,))
    profile = cur.fetchone()

    cur.execute("SELECT category_id FROM owner_categories WHERE owner_id=%s", (owner_id,))
    cat = cur.fetchone()
    if profile and cat:
        profile["category_id"] = cat["category_id"]

    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()

    return render_template(
        "owner/auth/signup_basic_info.html",
        profile=profile,
        categories=categories
    )
