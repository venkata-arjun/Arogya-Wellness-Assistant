import mysql.connector
import json


# Reusable function to get a DB connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Arjun@123",  # <- change this
        database="wellness_db",
    )


def save_history(
    user_id: str,
    user_message: str,
    final_json: dict,
    is_follow_up: bool,
    target_section: str | None,
):
    """
    Save one interaction to SQL.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        INSERT INTO wellness_history 
        (user_id, user_message, is_follow_up, target_section, final_json)
        VALUES (%s, %s, %s, %s, %s)
    """

    cur.execute(
        query,
        (
            user_id,
            user_message,
            is_follow_up,
            target_section,
            json.dumps(final_json, ensure_ascii=False),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def get_user_history(user_id: str, limit: int = 10):
    """
    Return recent rows from SQL for a given user.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = "SELECT * FROM wellness_history WHERE user_id=%s ORDER BY id DESC LIMIT %s"
    cur.execute(query, (user_id, limit))

    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


def get_last_interaction(user_id: str):
    """
    Get the most recent interaction for a user.
    Returns dict with user_message, final_json, and timestamp.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT user_message, final_json, created_at 
        FROM wellness_history 
        WHERE user_id=%s 
        ORDER BY id DESC 
        LIMIT 1
    """
    cur.execute(query, (user_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row and row.get("final_json"):
        try:
            row["final_json"] = json.loads(row["final_json"])
        except:
            pass

    return row
