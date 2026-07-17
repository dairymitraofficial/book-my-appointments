# ===============================
# FILE: book-my-appointments/customer/browse.py
# ===============================
from datetime import date

from flask import Blueprint, redirect, render_template, request, session
from extensions import get_db
from utils.security import customer_required

customer_browse_bp = Blueprint("customer_browse", __name__)

# ==================================================
# CATEGORIES
# ==================================================
@customer_browse_bp.route("/customer/categories")
@customer_required
def categories():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    return render_template(
        "customer/categories/categories.html",
        categories=categories,
        active_tab="search"
    )

# ==================================================
# OWNERS BY CATEGORY
# ==================================================
@customer_browse_bp.route("/customer/owners/<int:category_id>")
def owners(category_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*
        FROM owner_profiles p
        JOIN owner_categories oc ON p.owner_id = oc.owner_id
        WHERE oc.category_id = %s
    """, (category_id,))

    owners = cur.fetchall()

    return render_template(
        "customer/owners/owner_list.html",
        owners=owners,
        active_tab="search"
    )

# ==================================================
# SEARCH ALIAS
# ==================================================
@customer_browse_bp.route("/customer/search")
@customer_required
def customer_search_alias():
    return redirect("/customer/categories")

# ==================================================
# SERVICE DETAIL
# (original logic untouched + interest tracking added)
# ==================================================
@customer_browse_bp.route("/customer/service/<int:service_id>")
def customer_service_detail(service_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT s.*, o.business_name
        FROM services s
        JOIN owner_profiles o ON s.owner_id = o.owner_id
        WHERE s.id = %s
    """, (service_id,))
    service = cur.fetchone()

    if not service:
        return redirect("/customer/categories")

    cur.execute(
        "SELECT * FROM service_images WHERE service_id=%s",
        (service_id,)
    )
    images = cur.fetchall()

    # ===============================
    # 🔥 INTEREST TRACKING (SAFE)
    # ===============================
    if "customer_id" in session:
        # service view log (optional table)
        try:
            cur.execute("""
                INSERT INTO service_views (customer_id, service_id)
                VALUES (%s, %s)
            """, (session["customer_id"], service_id))
        except Exception:
            pass  # table optional, fail-safe

        # small interest boost (+1)
        cur.execute("""
            SELECT oc.category_id
            FROM owner_categories oc
            JOIN services s ON s.owner_id = oc.owner_id
            WHERE s.id = %s
            LIMIT 1
        """, (service_id,))
        row = cur.fetchone()

        if row:
            cur.execute("""
                INSERT INTO customer_interests (customer_id, category_id, score)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE score = score + 1
            """, (session["customer_id"], row["category_id"]))

        db.commit()

    return render_template(
        "customer/booking/service_detail.html",
        service=service,
        images=images,
        active_tab="search"
    )

# ==================================================
# OWNER PROFILE
# (original logic untouched + interest tracking added)
# ==================================================
@customer_browse_bp.route("/customer/owner/<int:owner_id>")
def owner_profile(owner_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM owner_profiles WHERE owner_id=%s",
        (owner_id,)
    )
    owner = cur.fetchone()

    if not owner:
        return redirect("/customer/categories")

    cur.execute("""
        SELECT s.*,
        (
            SELECT thumb_path
            FROM service_images
            WHERE service_id = s.id
            LIMIT 1
        ) AS thumb
        FROM services s
        WHERE s.owner_id = %s
    """, (owner_id,))
    services = cur.fetchall()

    # ===============================
    # 🔥 INTEREST TRACKING (SAFE)
    # ===============================
    if "customer_id" in session:
        cur.execute("""
            SELECT category_id
            FROM owner_categories
            WHERE owner_id = %s
        """, (owner_id,))

        rows = cur.fetchall()

        for r in rows:
            cur.execute("""
                INSERT INTO customer_interests (customer_id, category_id, score)
                VALUES (%s, %s, 2)
                ON DUPLICATE KEY UPDATE score = score + 2
            """, (session["customer_id"], r["category_id"]))

        db.commit()

    return render_template(
        "customer/owners/owner_profile.html",
        owner=owner,
        services=services,
        active_tab="search"
    )

# ==================================================
# SEARCH RESULTS
# (original query untouched + interest tracking added)
# ==================================================
@customer_browse_bp.route("/customer/search/results")
@customer_required
def search_results():
    q = request.args.get("q", "").strip()

    if not q:
        return redirect("/customer/categories")

    db = get_db()
    cur = db.cursor(dictionary=True)

    search = f"%{q}%"

    # ===============================
    # 🔥 INTEREST TRACKING (SAFE)
    # ===============================
    cur.execute("""
        SELECT id
        FROM categories
        WHERE name LIKE %s
    """, (search,))
    cats = cur.fetchall()

    for c in cats:
        cur.execute("""
            INSERT INTO customer_interests (customer_id, category_id, score)
            VALUES (%s, %s, 3)
            ON DUPLICATE KEY UPDATE score = score + 3
        """, (session["customer_id"], c["id"]))

    db.commit()

    # ===============================
    # ORIGINAL SEARCH QUERY (UNCHANGED)
    # ===============================
    cur.execute("""
        SELECT DISTINCT
            p.owner_id,
            p.full_name,
            p.business_name,
            p.address,
            p.profile_photo
        FROM owner_profiles p
        LEFT JOIN owner_categories oc ON p.owner_id = oc.owner_id
        LEFT JOIN categories c ON oc.category_id = c.id
        WHERE
            p.full_name LIKE %s
            OR p.business_name LIKE %s
            OR c.name LIKE %s
            OR p.address LIKE %s
            OR p.area LIKE %s
            OR p.district LIKE %s
    """, (
        search,
        search,
        search,
        search,
        search,
        search
    ))

    owners = cur.fetchall()

    return render_template(
        "customer/search/results.html",
        owners=owners,
        query=q,
        active_tab="search"
    )
