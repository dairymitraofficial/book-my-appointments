from flask import Blueprint, render_template, request, redirect, session, flash
from extensions import get_db
from utils.images import save_service_image
from utils.security import owner_required
import logging

owner_services_bp = Blueprint("owner_services", __name__)
logger = logging.getLogger(__name__)

@owner_services_bp.route("/owner/dashboard")
@owner_required
def owner_dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)

    owner_id = session["owner_id"]

    # =========================
    # OWNER PROFILE
    # =========================
    cur.execute("""
        SELECT
            o.email,
            op.full_name,
            op.business_name,
            op.address,
            op.profile_photo,
            op.description
        FROM owners o
        JOIN owner_profiles op ON op.owner_id = o.id
        WHERE o.id = %s
    """, (owner_id,))
    profile = cur.fetchone()

    # =========================
    # OWNER SERVICES
    # =========================
    cur.execute("""
    SELECT
        s.*,
        (
            SELECT thumb_path
            FROM service_images
            WHERE service_id = s.id
            LIMIT 1
        ) AS thumb
    FROM services s
    WHERE s.owner_id = %s
    ORDER BY s.created_at DESC
""", (owner_id,))

    services = cur.fetchall()

    # =========================
    # BOOKING STATS (OLD SCHEMA)
    # =========================
    cur.execute("""
        SELECT
            status,
            COUNT(*) AS total
        FROM bookings
        WHERE owner_id = %s
        GROUP BY status
    """, (owner_id,))
    booking_stats = {
        row["status"]: row["total"]
        for row in cur.fetchall()
    }

    # =========================
    # RENDER DASHBOARD
    # =========================
    return render_template(
        "owner/profile/profile.html",
        profile=profile,
        services=services,
        booking_stats=booking_stats,
        active_tab="account"
    )

@owner_services_bp.route("/owner/service/add", methods=["POST"])
@owner_required
def add_service():
    db = get_db()
    cur = db.cursor()

    try:
        service_name = request.form.get("service_name")
        original_price = request.form.get("original_price")
        price = request.form.get("price")
        description = request.form.get("description")
        files = request.files.getlist("images")

        # 🔒 BASIC VALIDATION
        if float(price) > float(original_price):
            flash("Current price cannot be greater than original price", "error")
            return redirect("/owner/dashboard")

        if not files or files[0].filename == "":
            flash("Please select at least one image", "error")
            return redirect("/owner/dashboard")

        cur.execute("""
            INSERT INTO services (
                owner_id,
                service_name,
                original_price,
                price,
                description
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session["owner_id"],
            service_name,
            original_price,
            price,
            description
        ))

        service_id = cur.lastrowid

        for i, file in enumerate(files):
            full, thumb = save_service_image(file, f"{service_id}_{i}")
            cur.execute("""
                INSERT INTO service_images (service_id, image_path, thumb_path)
                VALUES (%s, %s, %s)
            """, (service_id, full, thumb))

        db.commit()
        flash("Service added successfully", "success")

    except Exception as e:
        db.rollback()
        logger.exception("SERVICE UPLOAD FAILED")
        flash(f"Upload failed: {str(e)}", "error")

    return redirect("/owner/dashboard")


@owner_services_bp.route("/owner/service/<int:service_id>")
@owner_required
def service_detail(service_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM services WHERE id=%s AND owner_id=%s",
        (service_id, session["owner_id"])
    )
    service = cur.fetchone()

    if not service:
        flash("Service not found", "error")
        return redirect("/owner/dashboard")

    cur.execute(
        "SELECT * FROM service_images WHERE service_id=%s",
        (service_id,)
    )
    images = cur.fetchall()

    return render_template(
        "owner/services/service_detail.html",
        service=service,
        images=images
    )

@owner_services_bp.route("/owner/service/<int:service_id>/delete", methods=["POST"])
@owner_required
def delete_service(service_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔍 Check ownership
    cur.execute(
        "SELECT id FROM services WHERE id=%s AND owner_id=%s",
        (service_id, session["owner_id"])
    )
    service = cur.fetchone()

    if not service:
        flash("Service not found", "error")
        return redirect("/owner/dashboard")

    # 🔥 HARD BLOCK IF BOOKINGS EXIST
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM bookings WHERE service_id=%s",
        (service_id,)
    )
    booking_count = cur.fetchone()["cnt"]

    if booking_count > 0:
        flash(
            "This service already has bookings and cannot be deleted",
            "error"
        )
        # 🚫 THIS RETURN IS WHAT YOU WERE MISSING
        return redirect("/owner/dashboard")

    # ✅ Safe to delete
    try:
        cur.execute(
            "DELETE FROM service_images WHERE service_id=%s",
            (service_id,)
        )

        cur.execute(
            "DELETE FROM services WHERE id=%s AND owner_id=%s",
            (service_id, session["owner_id"])
        )

        db.commit()
        flash("Service deleted successfully", "success")

    except Exception as e:
        db.rollback()
        flash(f"Delete failed: {str(e)}", "error")

    return redirect("/owner/dashboard")

@owner_services_bp.route("/owner/service/<int:service_id>/edit", methods=["GET", "POST"])
@owner_required
def edit_service(service_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔍 Load service (ownership check)
    cur.execute(
        "SELECT * FROM services WHERE id=%s AND owner_id=%s",
        (service_id, session["owner_id"])
    )
    service = cur.fetchone()

    if not service:
        flash("Service not found", "error")
        return redirect("/owner/dashboard")

    if request.method == "POST":
        new_name = request.form["service_name"]
        new_original_price = request.form["original_price"]
        new_price = request.form["price"]
        new_desc = request.form["description"]

        # 🔒 Basic validation
        if float(new_price) > float(new_original_price):
            flash("Current price cannot be greater than original price", "error")
            return redirect(f"/owner/service/{service_id}/edit")

        # 🔥 Check booking count
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM bookings WHERE service_id=%s",
            (service_id,)
        )
        booking_count = int(cur.fetchone()["cnt"])

        # 🚫 If bookings exist, block BOTH price changes
        if booking_count > 0 and (
            float(new_price) != float(service["price"]) or
            float(new_original_price) != float(service["original_price"])
        ):
            flash(
                "Price cannot be changed because bookings already exist for this service",
                "error"
            )
            return redirect(f"/owner/service/{service_id}/edit")

        try:
            cur.execute("""
                UPDATE services
                SET service_name=%s,
                    original_price=%s,
                    price=%s,
                    description=%s
                WHERE id=%s AND owner_id=%s
            """, (
                new_name,
                new_original_price,
                new_price,
                new_desc,
                service_id,
                session["owner_id"]
            ))

            db.commit()
            flash("Service updated successfully", "success")
            return redirect(f"/owner/service/{service_id}")

        except Exception as e:
            db.rollback()
            flash(f"Update failed: {str(e)}", "error")
            return redirect(f"/owner/service/{service_id}/edit")

    # GET request
    return render_template(
        "owner/services/edit_service.html",
        service=service
    )

@owner_services_bp.route("/owner/profile")
@owner_required
def owner_profile_redirect():
    return redirect("/owner/dashboard")
