from extensions import get_db
from utils.push import send_push
from utils.emailer import send_email
import logging

logger = logging.getLogger(__name__)

def notify(user_id, role, title, body, email=None):
    print("🔔 NOTIFY FUNCTION HIT", user_id, role)

    db = get_db()
    cur = db.cursor(dictionary=True)

    # GET ALL TOKENS (single-device works fine too)
    cur.execute("""
        SELECT token
        FROM push_tokens
        WHERE user_id=%s AND role=%s
    """, (user_id, role))

    tokens = cur.fetchall()
    print("📱 TOKENS FOUND:", tokens)

    push_sent = False

    for row in tokens:
        token = row["token"]
        try:
            print("🚀 SENDING PUSH TO:", token)
            send_push(token, title, body)
            push_sent = True
        except Exception as e:
            logger.error("Push failed", exc_info=e)

    # EMAIL FALLBACK
    if not push_sent and email:
        print("📧 FALLBACK EMAIL TO:", email)
        send_email(email, title, body)
