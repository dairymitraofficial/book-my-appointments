from extensions import get_db

def get_or_create_conversation(owner_id, customer_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id FROM conversations
        WHERE owner_id=%s AND customer_id=%s
    """, (owner_id, customer_id))
    row = cur.fetchone()
    if row:
        return row["id"]

    cur.execute("""
        INSERT INTO conversations (owner_id, customer_id)
        VALUES (%s, %s)
    """, (owner_id, customer_id))
    db.commit()
    return cur.lastrowid
