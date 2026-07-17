from flask import Blueprint, render_template, session, request, redirect, jsonify
from extensions import get_db, csrf
from utils.security import owner_required
from utils.notifications import notify

owner_messages_bp = Blueprint("owner_messages", __name__)

# ==================================================
# OWNER MESSAGE THREAD LIST (INBOX)
# ==================================================
@owner_messages_bp.route("/owner/messages")
@owner_required
def owner_message_list():
    db = get_db()
    cur = db.cursor(dictionary=True)

    owner_id = session["owner_id"]

    cur.execute("""
        SELECT
            c.id AS conversation_id,
            cp.full_name AS customer_name,
            MAX(m.created_at) AS last_time,
            SUBSTRING_INDEX(
                GROUP_CONCAT(m.message ORDER BY m.created_at DESC),
                ',', 1
            ) AS last_message
        FROM conversations c
        JOIN customer_profiles cp ON cp.customer_id = c.customer_id
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE c.owner_id = %s
        GROUP BY c.id, cp.full_name
        ORDER BY last_time DESC
    """, (owner_id,))

    chats = cur.fetchall()

    return render_template(
        "owner/messages/list.html",
        chats=chats
    )

# ==================================================
# OWNER CHAT PAGE
# ==================================================
@owner_messages_bp.route("/owner/chat/<int:conversation_id>", methods=["GET", "POST"])
@owner_required
@csrf.exempt
def owner_chat(conversation_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔐 SECURITY CHECK
    cur.execute("""
        SELECT customer_id
        FROM conversations
        WHERE id=%s AND owner_id=%s
    """, (conversation_id, session["owner_id"]))

    convo = cur.fetchone()
    if not convo:
        return redirect("/owner/messages")

    customer_id = convo["customer_id"]

    # ======================
    # POST → SEND MESSAGE
    # ======================
    if request.method == "POST":
        message = request.form.get("message")

        if message:
            cur.execute("""
                INSERT INTO messages (conversation_id, sender, message)
                VALUES (%s, 'owner', %s)
            """, (conversation_id, message))
            db.commit()

            # 🔔 NOTIFY CUSTOMER
            notify(
                user_id=customer_id,
                role="customer",
                title="New Message",
                body=message[:120]
            )

        return redirect(f"/owner/chat/{conversation_id}")

    # ======================
    # GET → LOAD CHAT
    # ======================
    cur.execute("""
        SELECT sender, message
        FROM messages
        WHERE conversation_id=%s
        ORDER BY id ASC
    """, (conversation_id,))

    messages = cur.fetchall()

    return render_template(
        "owner/messages/chat.html",
        messages=messages,
        conversation_id=conversation_id
    )

# ==================================================
# OWNER REAL-TIME POLL (DELIVERED + SEEN + STATUS)
# ==================================================
@owner_messages_bp.route("/owner/chat/<int:conversation_id>/poll")
@owner_required
def owner_chat_poll(conversation_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # 🔐 SECURITY CHECK
    cur.execute("""
        SELECT id
        FROM conversations
        WHERE id=%s AND owner_id=%s
    """, (conversation_id, session["owner_id"]))

    if not cur.fetchone():
        return jsonify({"messages": []})

    # ======================
    # ✅ DELIVERED (customer → owner)
    # ======================
    cur.execute("""
        UPDATE messages
        SET delivered_at = NOW()
        WHERE conversation_id=%s
        AND sender='customer'
        AND delivered_at IS NULL
    """, (conversation_id,))

    # ======================
    # ✅ SEEN (customer → owner)
    # ======================
    cur.execute("""
        UPDATE messages
        SET seen_at = NOW()
        WHERE conversation_id=%s
        AND sender='customer'
        AND delivered_at IS NOT NULL
        AND seen_at IS NULL
    """, (conversation_id,))

    db.commit()

    # ======================
    # LOAD MESSAGES
    # ======================
    cur.execute("""
        SELECT sender, message, delivered_at, seen_at, created_at
        FROM messages
        WHERE conversation_id=%s
        ORDER BY created_at
    """, (conversation_id,))

    rows = cur.fetchall()

    # ======================
    # BUILD STATUS (BACKEND)
    # ======================
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
