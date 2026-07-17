from flask import Blueprint, request, redirect, session, flash
from extensions import get_db, csrf
from utils.security import customer_required
from datetime import date

customer_booking_bp = Blueprint("customer_booking", __name__)

# 🚫 BLOCK DIRECT ACCESS (GET)
@customer_booking_bp.route("/customer/book/<int:service_id>", methods=["GET"])
def block_direct_access(service_id):
    return redirect(f"/customer/service/{service_id}")

# ✅ REAL BOOKING (POST ONLY)
@customer_booking_bp.route("/customer/book/<int:service_id>", methods=["POST"])
@csrf.exempt
@customer_required
def book(service_id):
    booking_date = request.form.get("booking_date") or request.form.get("date")

    if not booking_date:
        flash("Please select booking date", "error")
        return redirect(f"/customer/service/{service_id}")

    # ✅ 1. PAST DATE BLOCK
    if booking_date < date.today().isoformat():
        flash("Past dates are not allowed", "error")
        return redirect(f"/customer/service/{service_id}")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔥 GET SERVICE OWNER
    cur.execute(
        "SELECT owner_id FROM services WHERE id=%s",
        (service_id,)
    )
    service = cur.fetchone()

    if not service:
        flash("Service not found", "error")
        return redirect("/customer/categories")

    # 🚫 2. SAME CUSTOMER + SAME SERVICE + SAME DATE (ONCE ONLY)
    cur.execute("""
        SELECT id FROM bookings
        WHERE customer_id=%s
          AND service_id=%s
          AND booking_date=%s
    """, (session["customer_id"], service_id, booking_date))

    if cur.fetchone():
        flash("You already requested this date for this service", "error")
        return redirect(f"/customer/service/{service_id}")

    # 🚫 3. DATE ALREADY ACCEPTED → FULLY BLOCK
    cur.execute("""
        SELECT id FROM bookings
        WHERE service_id=%s
          AND booking_date=%s
          AND status='accepted'
    """, (service_id, booking_date))

    if cur.fetchone():
        flash("This date is already booked", "error")
        return redirect(f"/customer/service/{service_id}")

    # ✅ INSERT (PENDING)
    cur.execute("""
        INSERT INTO bookings (
            service_id,
            owner_id,
            customer_id,
            booking_date,
            status
        )
        VALUES (%s, %s, %s, %s, 'pending')
    """, (
        service_id,
        service["owner_id"],
        session["customer_id"],
        booking_date
    ))

    db.commit()

    flash("Booking request sent successfully", "success")
    return redirect(f"/customer/owner/{service['owner_id']}")

from flask import jsonify
from extensions import get_db

@customer_booking_bp.route("/customer/service/<int:service_id>/disabled-dates")
@customer_required
def disabled_dates(service_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT booking_date
        FROM bookings
        WHERE service_id = %s
          AND status = 'accepted'
    """, (service_id,))

    dates = [row[0].strftime("%Y-%m-%d") for row in cur.fetchall()]

    return jsonify(dates)
