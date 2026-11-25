import sqlite3
import datetime

import init


DB_PATH = init.DB_PATH


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def grant_monthly_credit(student_id, year, month):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                student_id,
                lessons_per_month,
                granted_at
            FROM student_monthly_plans
            WHERE student_id = ?
                AND year = ?
                AND month = ?
            """,
            (student_id, year, month)
        )

        result = cursor.fetchone()

        if result is None:
            print("Error: plan is not found.")
            return

        if result[2] is not None:
            print("ERror: monthly lessons have already been granted.")
            return

        plan_student_id, lessons_per_month, granted_at = result

        now = datetime.datetime.now().isoformat(timespec="seconds")

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
                plan_student_id,
                lessons_per_month,
                "monthly_grant",
                now,
                None
            )
        )

        cursor.execute(
            """
            UPDATE student_monthly_plans
            SET granted_at = ?
            WHERE student_id = ?
                AND year = ?
                AND month = ?
            """,
            (
                now, 
                plan_student_id,
                year,
                month
            )
        )

        connection.commit()

        print(
            f"Monthly credit granted: "
            f"student_id={plan_student_id}, "
            f"amount={lessons_per_month}"
        )

    except sqlite3.Error as e:
        connection.rollback()
        print(f"Database error: {e}")

    finally:
        connection.close()
