from datetime import datetime, timedelta
import random
from extensions import get_db
from flask import flash


def create_otp(email, role):
    db = get_db()
    cur = db.cursor()

    # 🔁 RESET old OTP attempts & lock (THIS IS THE ANSWER)
    cur.execute("""
        UPDATE otp_verifications
        SET attempts = 0,
            locked_until = NULL
        WHERE email = %s AND role = %s
    """, (email, role))

    otp = str(random.randint(100000, 999999))

    cur.execute("""
        INSERT INTO otp_verifications
        (email, role, otp_code, expires_at, attempts)
        VALUES (%s, %s, %s, %s, 0)
    """, (
        email,
        role,
        otp,
        datetime.now() + timedelta(minutes=2)
    ))

    db.commit()
    return otp




MAX_ATTEMPTS = 5
LOCK_MINUTES = 15

def verify_otp(email, role, otp):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM otp_verifications
        WHERE email=%s AND role=%s
        ORDER BY id DESC
        LIMIT 1
    """, (email, role))
    r = cur.fetchone()

    # ❌ No OTP found or expired
    if not r or r["expires_at"] < datetime.now():
        return False

    # 🔒 HARD LOCK CHECK
    if r.get("locked_until") and datetime.now() < r["locked_until"]:
        return False

    # ✅ OTP MATCH
    if r["otp_code"] == otp:
        cur.execute("""
            UPDATE otp_verifications
            SET attempts=0, locked_until=NULL
            WHERE id=%s
        """, (r["id"],))
        db.commit()
        return True

    # ❌ OTP WRONG
    attempts = (r["attempts"] or 0) + 1

    # 🔒 Lock if max attempts reached
    if attempts >= MAX_ATTEMPTS:
        cur.execute("""
            UPDATE otp_verifications
            SET attempts=%s,
                locked_until=%s
            WHERE id=%s
        """, (
            attempts,
            datetime.now() + timedelta(minutes=LOCK_MINUTES),
            r["id"]
        ))
        db.commit()
        return False

    # ❌ Normal wrong attempt
    cur.execute("""
        UPDATE otp_verifications
        SET attempts=%s
        WHERE id=%s
    """, (attempts, r["id"]))
    db.commit()

    return False

