from flask import Blueprint, render_template, session, redirect
from extensions import get_db
from utils.security import customer_required

customer_account_bp = Blueprint("customer_account", __name__)

# ===============================
# CUSTOMER ACCOUNT (PROFILE VIEW)
# ===============================
@customer_account_bp.route("/customer/account")
@customer_required
def customer_account():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM customer_profiles
        WHERE customer_id = %s
    """, (session["customer_id"],))
    profile = cur.fetchone()

    if not profile:
        return redirect("/customer/categories")

    return render_template(
        "customer/account/account.html",
        profile=profile,
        active_tab="account"
    )

# ===============================
# CUSTOMER REQUESTS (BOOKINGS)
# ===============================
@customer_account_bp.route("/customer/account/requests")
@customer_required
def customer_requests():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            b.id AS booking_id,
            b.booking_date,
            b.status,
            s.service_name,
            o.business_name
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN owner_profiles o ON b.owner_id = o.owner_id
        WHERE b.customer_id = %s
        ORDER BY b.created_at DESC
    """, (session["customer_id"],))

    bookings = cur.fetchall()

    return render_template(
        "customer/account/requests.html",
        bookings=bookings,
        active_tab="account"
    )
