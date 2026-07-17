from flask import Flask, session, g
from config import *
from extensions import csrf
import logging
import os
from extensions import get_db
from core.routes import core_bp
from auth.owner import owner_auth_bp
from auth.customer import customer_auth_bp
from owner.services import owner_services_bp
from owner.bookings import owner_bookings_bp
from customer.browse import customer_browse_bp
from customer.booking import customer_booking_bp
from customer.account import customer_account_bp
from customer.messages import customer_messages_bp
from owner.messages import owner_messages_bp
from flask import send_from_directory
from datetime import datetime
from owner.account import owner_account_bp
from config import Config
from customer.feed import customer_feed_bp



app = Flask(__name__)

# ✅ LOAD CONFIG (ONLY SOURCE OF SESSION SETTINGS)
app.config.from_object(Config)

# ✅ CSRF INIT
csrf.init_app(app)

# ===============================
# SERVICE WORKER
# ===============================
@app.route("/firebase-messaging-sw.js")
def firebase_service_worker():
    return send_from_directory(
        directory=os.path.dirname(os.path.abspath(__file__)),
        path="firebase-messaging-sw.js",
        mimetype="application/javascript"
    )

# ===============================
# DB CLOSE
# ===============================
@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ===============================
# LOGGING
# ===============================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ===============================
# BLUEPRINTS
# ===============================
app.register_blueprint(core_bp)
app.register_blueprint(owner_auth_bp)
app.register_blueprint(customer_auth_bp)
app.register_blueprint(owner_services_bp)
app.register_blueprint(owner_bookings_bp)
app.register_blueprint(customer_browse_bp)
app.register_blueprint(customer_booking_bp)
app.register_blueprint(customer_account_bp)
app.register_blueprint(customer_messages_bp)
app.register_blueprint(owner_messages_bp)
app.register_blueprint(owner_account_bp)
app.register_blueprint(customer_feed_bp)

# ===============================
# USER PRESENCE (SAFE)
# ===============================
@app.before_request
def track_presence():
    if "role" not in session:
        return

    if "customer_id" in session:
        user_id = session["customer_id"]
        role = "customer"
    elif "owner_id" in session:
        user_id = session["owner_id"]
        role = "owner"
    else:
        return

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO user_presence (user_id, role, last_seen)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE last_seen=%s
    """, (user_id, role, datetime.now(), datetime.now()))
    db.commit()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
