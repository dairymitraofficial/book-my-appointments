from flask import Blueprint, render_template, session, jsonify, request
from extensions import get_db, csrf
from utils.security import customer_required

customer_feed_bp = Blueprint("customer_feed", __name__)

# ==================================================
# CUSTOMER FEED (REELS / POSTS)
# ==================================================
@customer_feed_bp.route("/customer/feed")
@customer_required
def customer_feed():
    db = get_db()
    cur = db.cursor(dictionary=True)

    customer_id = session["customer_id"]

    # 1️⃣ USER INTERESTS
    cur.execute("""
        SELECT category_id
        FROM customer_interests
        WHERE customer_id = %s
        ORDER BY score DESC
        LIMIT 5
    """, (customer_id,))
    interests = cur.fetchall()
    category_ids = [row["category_id"] for row in interests]

    # 2️⃣ FEED POSTS
    if category_ids:
        placeholders = ",".join(["%s"] * len(category_ids))
        query = f"""
            SELECT
                s.id AS service_id,
                s.service_name,
                s.price,
                op.business_name,
                op.owner_id,
                op.profile_photo,
                (
                    SELECT thumb_path
                    FROM service_images
                    WHERE service_id = s.id
                    LIMIT 1
                ) AS image,
                (
                    SELECT COUNT(*)
                    FROM post_likes
                    WHERE service_id = s.id
                ) AS like_count,
                (
                    SELECT 1
                    FROM post_likes
                    WHERE service_id = s.id
                      AND customer_id = %s
                ) AS liked
            FROM services s
            JOIN owner_categories oc ON s.owner_id = oc.owner_id
            JOIN owner_profiles op ON op.owner_id = s.owner_id
            WHERE oc.category_id IN ({placeholders})
            ORDER BY RAND()
            LIMIT 30
        """
        cur.execute(query, (customer_id, *category_ids))
    else:
        cur.execute("""
            SELECT
                s.id AS service_id,
                s.service_name,
                s.price,
                op.business_name,
                op.owner_id,
                op.profile_photo,
                (
                    SELECT thumb_path
                    FROM service_images
                    WHERE service_id = s.id
                    LIMIT 1
                ) AS image,
                (
                    SELECT COUNT(*)
                    FROM post_likes
                    WHERE service_id = s.id
                ) AS like_count,
                NULL AS liked
            FROM services s
            JOIN owner_profiles op ON op.owner_id = s.owner_id
            ORDER BY s.created_at DESC
            LIMIT 30
        """)

    posts = cur.fetchall()

    return render_template(
        "customer/feed/feed.html",
        posts=posts,
        active_tab="feed"
    )

# ==================================================
# ❤️ LIKE POST
# ==================================================
@customer_feed_bp.route("/customer/post/<int:service_id>/like", methods=["POST"])
@csrf.exempt
@customer_required
def like_post(service_id):
    db = get_db()
    cur = db.cursor()

    customer_id = session["customer_id"]

    cur.execute("""
        INSERT IGNORE INTO post_likes (customer_id, service_id)
        VALUES (%s, %s)
    """, (customer_id, service_id))

    # UPDATE INTEREST SCORE
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
            VALUES (%s, %s, 5)
            ON DUPLICATE KEY UPDATE score = score + 5
        """, (customer_id, row[0]))

    cur.execute("""
        SELECT COUNT(*) FROM post_likes WHERE service_id = %s
    """, (service_id,))
    likes = cur.fetchone()[0]

    db.commit()
    return jsonify({"likes": likes})

# ==================================================
# 🤍 UNLIKE POST
# ==================================================
@customer_feed_bp.route("/customer/post/<int:service_id>/unlike", methods=["POST"])
@csrf.exempt
@customer_required
def unlike_post(service_id):
    db = get_db()
    cur = db.cursor()

    customer_id = session["customer_id"]

    cur.execute("""
        DELETE FROM post_likes
        WHERE customer_id = %s AND service_id = %s
    """, (customer_id, service_id))

    cur.execute("""
        SELECT COUNT(*) FROM post_likes WHERE service_id = %s
    """, (service_id,))
    likes = cur.fetchone()[0]

    db.commit()
    return jsonify({"likes": likes})

@customer_feed_bp.route("/customer/feed/load")
@customer_required
def load_more_feed():
    offset = int(request.args.get("offset", 0))
    limit = 10

    db = get_db()
    cur = db.cursor(dictionary=True)

    customer_id = session["customer_id"]

    cur.execute("""
        SELECT
            s.id AS service_id,
            s.service_name,
            s.price,
            op.business_name,
            op.owner_id,
            op.profile_photo,
            (
                SELECT thumb_path
                FROM service_images
                WHERE service_id = s.id
                LIMIT 1
            ) AS image,
            (
                SELECT COUNT(*)
                FROM post_likes
                WHERE service_id = s.id
            ) AS like_count,
            (
                SELECT 1
                FROM post_likes
                WHERE service_id = s.id
                  AND customer_id = %s
            ) AS liked
        FROM services s
        JOIN owner_profiles op ON op.owner_id = s.owner_id
        ORDER BY RAND()
        LIMIT %s OFFSET %s
    """, (customer_id, limit, offset))

    posts = cur.fetchall()
    return jsonify(posts)
