import sqlite3

import pytest

import init

from grant_monthly_lessons import grant_monthly_credit
from complete_lesson import confirm_complete_lesson
from reschedule_lesson import execute_reschedule


def get_connection():
    connection = sqlite3.connect(init.DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@pytest.fixture(autouse=True)
def reset_database():
    init.main()


def test_grant():
    grant_monthly_credit(1, 2026, 10)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            student_id,
            change_amount,
            reason
        FROM lesson_credit_transactions
        WHERE student_id = ?
        """,
        (1,)
    )

    trans_result = cursor.fetchone()

    assert trans_result is not None
    assert trans_result == (
        1,
        4,
        "monthly_grant"
    )

    cursor.execute(
        """
        SELECT granted_at
        FROM student_monthly_plans
        WHERE student_id = ?
          AND year = ?
          AND month = ?
        """,
        (
            1,
            2026,
            10
        )
    )

    grant_result = cursor.fetchone()

    assert grant_result is not None
    assert grant_result[0] is not None

    connection.close()


def test_prevent_double_grant():
    grant_monthly_credit(1, 2026, 10)
    grant_monthly_credit(1, 2026, 10)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            SUM(change_amount)
        FROM lesson_credit_transactions
        WHERE student_id = ?
        """,
        (1,)
    )

    double_grant_result = cursor.fetchone()

    assert double_grant_result == (1, 4)

    connection.close()


def test_nonexistent_plan_grant(capsys):
    grant_monthly_credit(1, 2026, 11)

    captured = capsys.readouterr()

    assert (
        "Error: plan is not found."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lesson_credit_transactions
        WHERE student_id = ?
        """,
        (1,)
    )

    wrong_grant_result = cursor.fetchone()

    assert wrong_grant_result == (0,)

    connection.close()


def test_complete_lesson():
    confirm_complete_lesson(1)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lesson_state
        FROM lessons
        WHERE lesson_id = ?
        """,
        (1,)
    )

    complete_lesson_result = cursor.fetchone()

    assert complete_lesson_result == (
        "completed",
    )

    cursor.execute(
        """
        SELECT
            student_id,
            change_amount,
            reason,
            lesson_id
        FROM lesson_credit_transactions
        WHERE lesson_id = ?
        """,
        (1,)
    )

    complete_transaction_result = cursor.fetchone()

    assert complete_transaction_result == (
        1,
        -1,
        "lesson_completed",
        1
    )

    connection.close()


def test_prevent_double_complete(capsys):
    confirm_complete_lesson(1)
    confirm_complete_lesson(1)

    captured = capsys.readouterr()

    assert (
        "Error: lesson is already completed."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            SUM(change_amount)
        FROM lesson_credit_transactions
        WHERE reason = ?
          AND lesson_id = ?
        """,
        (
            "lesson_completed",
            1
        )
    )

    double_complete_result = cursor.fetchone()

    assert double_complete_result == (
        1,
        -1
    )

    connection.close()


def test_complete_nonexistent_lesson(capsys):
    confirm_complete_lesson(999)

    captured = capsys.readouterr()

    assert (
        "Error: lesson is not found."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lesson_credit_transactions
        """
    )

    result = cursor.fetchone()

    assert result == (0,)

    connection.close()


def test_canceled_lesson_complete(capsys):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE lessons
        SET lesson_state = ?
        WHERE lesson_id = ?
        """,
        (
            "canceled",
            1
        )
    )

    connection.commit()
    connection.close()

    confirm_complete_lesson(1)

    captured = capsys.readouterr()

    assert (
        "Error: lesson is already canceled."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lesson_state
        FROM lessons
        WHERE lesson_id = ?
        """,
        (1,)
    )

    canceled_lesson_result = cursor.fetchone()

    assert canceled_lesson_result == (
        "canceled",
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lesson_credit_transactions
        WHERE lesson_id = ?
        """,
        (1,)
    )

    canceled_transaction_result = cursor.fetchone()

    assert canceled_transaction_result == (0,)

    connection.close()


def test_rescheduled_lesson_complete(capsys):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE lessons
        SET lesson_state = ?
        WHERE lesson_id = ?
        """,
        (
            "rescheduled",
            1
        )
    )

    connection.commit()
    connection.close()

    confirm_complete_lesson(1)

    captured = capsys.readouterr()

    assert (
        "Error: lesson is already rescheduled."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lesson_state
        FROM lessons
        WHERE lesson_id = ?
        """,
        (1,)
    )

    rescheduled_lesson_result = cursor.fetchone()

    assert rescheduled_lesson_result == (
        "rescheduled",
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lesson_credit_transactions
        WHERE lesson_id = ?
        """,
        (1,)
    )

    rescheduled_transaction_result = cursor.fetchone()

    assert rescheduled_transaction_result == (0,)

    connection.close()


def test_reschedule_without_instructor_subject():
    execute_reschedule(
        1,
        "2026-10-17",
        1
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT lesson_state
        FROM lessons
        WHERE lesson_id = ?
        """,
        (1,)
    )

    pre_lesson_state_result = cursor.fetchone()

    assert pre_lesson_state_result == (
        "rescheduled",
    )

    cursor.execute(
        """
        SELECT
            student_id,
            instructor_id,
            subject_id,
            time_slot_id,
            lesson_date,
            lesson_state,
            rescheduled_from_lesson_id
        FROM lessons
        WHERE rescheduled_from_lesson_id = ?
        """,
        (1,)
    )

    result = cursor.fetchone()

    assert result is not None

    assert result == (
        1,
        None,
        1,
        1,
        "2026-10-17",
        "scheduled",
        1
    )

    cursor.execute(
        """
        SELECT 1
        FROM lesson_credit_transactions
        LIMIT 1
        """
    )

    transaction_result = cursor.fetchone()

    assert transaction_result is None

    connection.close()


def test_reschedule_with_instructor_and_subject():
    execute_reschedule(
        1,
        "2026-10-17",
        1,
        2,
        2
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            student_id,
            instructor_id,
            subject_id,
            time_slot_id,
            lesson_date,
            lesson_state,
            rescheduled_from_lesson_id
        FROM lessons
        WHERE rescheduled_from_lesson_id = ?
        """,
        (1,)
    )

    result = cursor.fetchone()

    assert result is not None

    assert result == (
        1,
        2,
        2,
        1,
        "2026-10-17",
        "scheduled",
        1
    )

    connection.close()


def test_reschedule_rejects_student_conflict(capsys):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO lessons (
            lesson_id,
            student_id,
            instructor_id,
            subject_id,
            time_slot_id,
            lesson_date,
            lesson_state,
            rescheduled_from_lesson_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            None,
            1,
            2,
            1,
            1,
            "2026-10-17",
            "scheduled",
            None
        )
    )
    
    reserved_lesson_id = cursor.lastrowid

    connection.commit()
    connection.close()

    execute_reschedule(1, "2026-10-17", 1, 1, 1)
    captured = capsys.readouterr()

    assert (
        "Error: Lesson for this student is already scheduled."
        in captured.out
    )

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                student_id,
                instructor_id,
                time_slot_id,
                lesson_date,
                lesson_state
            FROM lessons
            WHERE lesson_id = ?           
            """,
            (1,)
        )

        result_origin_lesson_status = cursor.fetchone()

        assert result_origin_lesson_status == (1, 1, 1, "2026-10-10", "scheduled")

        cursor.execute(
            """
            SELECT lesson_id, lesson_state
            FROM lessons
            WHERE student_id = ?
              AND time_slot_id = ?
              AND lesson_date = ?
            """,
            (1, 1, "2026-10-17")
        )

        result_destination_lessons = cursor.fetchall()
        assert result_destination_lessons == [(reserved_lesson_id, "scheduled")]

    finally:
        connection.close()


def test_reschedule_reject_instructor_conflict(capsys):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO lessons (
            lesson_id,
            student_id,
            instructor_id,
            subject_id,
            time_slot_id,
            lesson_date,
            lesson_state,
            rescheduled_from_lesson_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (None, 2, 1, 1, 1, "2026-10-17", "scheduled", None)
    )
    
    reserved_lesson_id = cursor.lastrowid

    connection.commit()
    connection.close()

    execute_reschedule(1, "2026-10-17", 1, 1, 1)

    captured = capsys.readouterr()
    assert ("Error: Lesson for this instructor is already scheduled." in captured.out)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            student_id,
            instructor_id,
            time_slot_id,
            lesson_date,
            lesson_state
        FROM lessons
        WHERE lesson_id = ?
        """,
        (1,)
    )

    result_origin_lesson_status = cursor.fetchone()
    assert result_origin_lesson_status == (1, 1, 1, "2026-10-10", "scheduled")

    cursor.execute(
        """
        SELECT lesson_id, lesson_state
        FROM lessons
        WHERE instructor_id = ?
            AND time_slot_id = ?
            AND lesson_date = ?
        """,
        (1, 1, "2026-10-17")
    )

    result_destination_lessons = cursor.fetchall()
    assert result_destination_lessons == [(reserved_lesson_id, "scheduled")]

    connection.close()
