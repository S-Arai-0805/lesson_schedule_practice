import sqlite3
import datetime

import init


DB_PATH = init.DB_PATH


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def confirm_complete_lesson(lesson_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                student_id,
                lesson_state
            FROM lessons
            WHERE lesson_id = ?
            """,
            (lesson_id,)
        )

        lesson_result = cursor.fetchone()

        if lesson_result is None:
            print("Error: lesson is not found.")
            return

        student_id, lesson_state = lesson_result

        if lesson_state == "completed":
            print("Error: lesson is already completed.")
            return

        if lesson_state == "canceled":
            print("Error: lesson is already canceled.")
            return

        if lesson_state == "rescheduled":
            print("Error: lesson is already rescheduled.")
            return

        cursor.execute(
            """
            UPDATE lessons
            SET lesson_state = ?
            WHERE lesson_id = ?
            """,
            (
                "completed",
                lesson_id
            )
        )

        now = datetime.datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO lesson_credit_transactions (
                student_id,
                change_amount,
                reason,
                transaction_date,
                lesson_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                student_id,
                -1,
                "lesson_completed",
                now,
                lesson_id
            )
        )

        connection.commit()

    except sqlite3.Error as e:
        connection.rollback()
        print(f"Database error: {e}")

    finally:
        connection.close()
