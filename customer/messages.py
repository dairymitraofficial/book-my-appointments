from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for
from extensions import get_db, csrf
from utils.security import customer_required
from utils.notifications import notify

customer_messages_bp = Blueprint("customer_messages", __name__)

# ==================================================
# CUSTOMER MESSAGE LIST (INBOX)
# ==================================================
@customer_messages_bp.route("/customer/messages")
@customer_required
def customer_message_list():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            c.id AS conversation_id,
            op.business_name,
            op.profile_photo,
            MAX(m.created_at) AS last_time,
            SUBSTRING_INDEX(
                GROUP_CONCAT(m.message ORDER BY m.created_at DESC),
                ',', 1
            ) AS last_message
        FROM conversations c
        JOIN owner_profiles op ON op.owner_id = c.owner_id
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE c.customer_id = %s
        GROUP BY c.id, op.business_name, op.profile_photo
        ORDER BY last_time DESC
    """, (session["customer_id"],))

    chats = cur.fetchall()

    return render_template(
        "customer/messages/list.html",
        chats=chats,
        active_tab="messages"
    )

# ==================================================
# CUSTOMER CHAT PAGE
# ==================================================
@customer_messages_bp.route("/customer/chat/<int:conversation_id>", methods=["GET", "POST"])
@customer_required
@csrf.exempt
def customer_chat(conversation_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔐 SECURITY CHECK
    cur.execute("""
        SELECT owner_id
        FROM conversations
        WHERE id=%s AND customer_id=%s
    """, (conversation_id, session["customer_id"]))

    convo = cur.fetchone()
    if not convo:
        return redirect("/customer/messages")

    owner_id = convo["owner_id"]

    # ===============================
    # POST → SEND MESSAGE
    # ===============================
    if request.method == "POST":
        message = request.form.get("message")

        if message:
            cur.execute("""
                INSERT INTO messages (conversation_id, sender, message)
                VALUES (%s, 'customer', %s)
            """, (conversation_id, message))
            db.commit()

            # 🔔 NOTIFY OWNER
            notify(
                user_id=owner_id,
                role="owner",
                title="New Message",
                body=message[:120]
            )

        return redirect(f"/customer/chat/{conversation_id}")

    # ===============================
    # GET → LOAD CHAT (INITIAL LOAD)
    # ===============================
    cur.execute("""
        SELECT sender, message
        FROM messages
        WHERE conversation_id=%s
        ORDER BY id ASC
    """, (conversation_id,))

    messages = cur.fetchall()

    return render_template(
        "customer/messages/chat.html",
        messages=messages,
        conversation_id=conversation_id
    )

# ==================================================
# CUSTOMER + OWNER COMMON POLL (REAL-TIME)
# ==================================================
@customer_messages_bp.route("/chat/poll/<int:conversation_id>")
def chat_poll(conversation_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔒 SECURITY (customer OR owner)
    cur.execute("""
        SELECT customer_id, owner_id
        FROM conversations
        WHERE id=%s
        AND (customer_id=%s OR owner_id=%s)
    """, (
        conversation_id,
        session.get("customer_id", 0),
        session.get("owner_id", 0)
    ))

    convo = cur.fetchone()
    if not convo:
        return jsonify({"messages": []})

    is_customer = "customer_id" in session
    is_owner = "owner_id" in session

    # ===============================
    # CUSTOMER VIEWING → OWNER msgs
    # ===============================
    if is_customer:
        cur.execute("""
            UPDATE messages
            SET delivered_at = NOW()
            WHERE conversation_id=%s
            AND sender='owner'
            AND delivered_at IS NULL
        """, (conversation_id,))

        cur.execute("""
            UPDATE messages
            SET seen_at = NOW()
            WHERE conversation_id=%s
            AND sender='owner'
            AND delivered_at IS NOT NULL
            AND seen_at IS NULL
        """, (conversation_id,))

    # ===============================
    # OWNER VIEWING → CUSTOMER msgs
    # ===============================
    if is_owner:
        cur.execute("""
            UPDATE messages
            SET delivered_at = NOW()
            WHERE conversation_id=%s
            AND sender='customer'
            AND delivered_at IS NULL
        """, (conversation_id,))

        cur.execute("""
            UPDATE messages
            SET seen_at = NOW()
            WHERE conversation_id=%s
            AND sender='customer'
            AND delivered_at IS NOT NULL
            AND seen_at IS NULL
        """, (conversation_id,))

    db.commit()

    # ===============================
    # LOAD MESSAGES
    # ===============================
    cur.execute("""
        SELECT sender, message, delivered_at, seen_at, created_at
        FROM messages
        WHERE conversation_id=%s
        ORDER BY created_at
    """, (conversation_id,))

    rows = cur.fetchall()

    messages = []
    for m in rows:
        status = "sent"
        if m["delivered_at"]:
            status = "delivered"
        if m["seen_at"]:
            status = "seen"

        messages.append({
            "sender": m["sender"],
            "message": m["message"],
            "created_at": m["created_at"],
            "status": status
        })

    return jsonify({"messages": messages})

# ==================================================
# CUSTOMER → START MESSAGE (BEFORE BOOKING)
# ==================================================
@customer_messages_bp.route("/customer/message/start/<int:owner_id>", methods=["POST"])
@customer_required
@csrf.exempt
def start_message(owner_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    customer_id = session["customer_id"]

    # conversation already exists?
    cur.execute("""
        SELECT id FROM conversations
        WHERE owner_id=%s AND customer_id=%s
    """, (owner_id, customer_id))

    convo = cur.fetchone()

    if not convo:
        cur.execute("""
            INSERT INTO conversations (owner_id, customer_id)
            VALUES (%s, %s)
        """, (owner_id, customer_id))
        db.commit()
        conversation_id = cur.lastrowid
    else:
        conversation_id = convo["id"]

    return redirect(
        url_for("customer_messages.customer_chat", conversation_id=conversation_id)
    )
