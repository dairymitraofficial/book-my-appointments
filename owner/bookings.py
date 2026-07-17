from flask import Blueprint, render_template, jsonify, session
from extensions import get_db, csrf
from utils.security import owner_required
from utils.emailer import send_email
from datetime import date

owner_bookings_bp = Blueprint("owner_bookings", __name__)

# =====================================================
# SHOW ONLY BOOKING DATES
# =====================================================
@owner_bookings_bp.route("/owner/bookings")
@owner_required
def booked_calendar():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT DISTINCT booking_date
        FROM bookings
        WHERE owner_id = %s
        ORDER BY booking_date ASC
    """, (session["owner_id"],))

    dates = cur.fetchall()

    return render_template(
        "owner/bookings/booked_calendar.html",
        dates=dates
    )

# =====================================================
# BOOKINGS OF A DATE (AJAX)
# =====================================================
@owner_bookings_bp.route("/owner/bookings/date/<date>")
@owner_required
def bookings_by_date(date):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            b.id,
            b.status,
            s.service_name,
            cp.full_name AS customer_name,
            c.email
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN customers c ON b.customer_id = c.id
        JOIN customer_profiles cp ON cp.customer_id = c.id
        WHERE b.owner_id = %s AND b.booking_date = %s
    """, (session["owner_id"], date))

    return jsonify(cur.fetchall())

# =====================================================
# ACCEPT BOOKING
# =====================================================
@owner_bookings_bp.route("/owner/booking/<int:booking_id>/accept", methods=["POST"])
@csrf.exempt
@owner_required
def accept_booking(booking_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔍 GET BOOKING INFO
    cur.execute("""
        SELECT
            b.id,
            b.service_id,
            b.booking_date,
            b.customer_id,
            c.email
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = %s AND b.owner_id = %s
    """, (booking_id, session["owner_id"]))

    booking = cur.fetchone()
    if not booking:
        return jsonify({"error": "Invalid booking"}), 404

    # 🚫 BLOCK IF DATE ALREADY ACCEPTED
    cur.execute("""
        SELECT id FROM bookings
        WHERE service_id=%s
          AND booking_date=%s
          AND status='accepted'
    """, (booking["service_id"], booking["booking_date"]))

    if cur.fetchone():
        return jsonify({"error": "Date already booked"}), 400

    # ✅ ACCEPT BOOKING
    cur.execute("""
        UPDATE bookings
        SET status='accepted'
        WHERE id=%s
    """, (booking_id,))

    # ❌ REJECT OTHER PENDING BOOKINGS
    cur.execute("""
        UPDATE bookings
        SET status='rejected'
        WHERE service_id=%s
          AND booking_date=%s
          AND status='pending'
          AND id != %s
    """, (
        booking["service_id"],
        booking["booking_date"],
        booking_id
    ))

    # ===============================
    # 🔥 AUTO CHAT MESSAGE (NEW)
    # ===============================
    from utils.conversations import get_or_create_conversation

    conversation_id = get_or_create_conversation(
        owner_id=session["owner_id"],
        customer_id=booking["customer_id"]
    )

    cur.execute("""
        INSERT INTO messages (conversation_id, sender, message)
        VALUES (%s, 'owner', %s)
    """, (
        conversation_id,
        f"✅ Your booking for {booking['booking_date']} has been accepted."
    ))

    db.commit()

    # 🔔 NOTIFY CUSTOMER
    from utils.notifications import notify

    notify(
        user_id=booking["customer_id"],
        role="customer",
        title="Booking Accepted",
        body=f"Your booking for {booking['booking_date']} has been accepted",
        email=booking["email"]
    )

    return jsonify({"success": True})


# =====================================================
# REJECT BOOKING
# =====================================================
@owner_bookings_bp.route("/owner/booking/<int:booking_id>/reject", methods=["POST"])
@csrf.exempt
@owner_required
def reject_booking(booking_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔍 GET BOOKING INFO
    cur.execute("""
        SELECT
            b.customer_id,
            b.booking_date,
            c.email
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = %s AND b.owner_id = %s
    """, (booking_id, session["owner_id"]))

    booking = cur.fetchone()
    if not booking:
        return jsonify({"error": "Invalid booking"}), 404

    # ❌ REJECT BOOKING
    cur.execute("""
        UPDATE bookings
        SET status='rejected'
        WHERE id=%s AND owner_id=%s
    """, (booking_id, session["owner_id"]))

    # ===============================
    # 🔥 AUTO CHAT MESSAGE (NEW)
    # ===============================
    from utils.conversations import get_or_create_conversation

    conversation_id = get_or_create_conversation(
        owner_id=session["owner_id"],
        customer_id=booking["customer_id"]
    )

    cur.execute("""
        INSERT INTO messages (conversation_id, sender, message)
        VALUES (%s, 'owner', %s)
    """, (
        conversation_id,
        f"❌ Your booking for {booking['booking_date']} has been rejected."
    ))

    db.commit()

    # 🔔 NOTIFY CUSTOMER
    from utils.notifications import notify

    notify(
        user_id=booking["customer_id"],
        role="customer",
        title="Booking Rejected",
        body=f"Your booking for {booking['booking_date']} was rejected",
        email=booking["email"]
    )

    return jsonify({"success": True})


@owner_bookings_bp.route("/owner/schedule")
@owner_required
def owner_schedule():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            b.booking_date,
            cp.full_name AS customer_name,
            cp.address AS customer_address,
            s.service_name
        FROM bookings b
        JOIN customer_profiles cp ON cp.customer_id = b.customer_id
        JOIN services s ON s.id = b.service_id
        WHERE
            b.owner_id = %s
            AND b.status = 'accepted'
        ORDER BY b.booking_date ASC
    """, (session["owner_id"],))

    schedules = cur.fetchall()

    return render_template(
        "owner/schedule/schedule.html",
        schedules=schedules,
        active_tab="schedule"
    )
