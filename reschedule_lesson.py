import sqlite3

import init


def get_conneciton():
    connection = sqlite3.connect(init.DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def execute_reschedule(
        pre_lesson_id,
        new_lesson_date,
        new_time_slot_id,
        new_instructor_id=None,
        new_subject_id=None
):
    connection = get_conneciton()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                student_id,
                subject_id,
                lesson_state
            FROM lessons
            WHERE lesson_id = ?
            """,
            (pre_lesson_id,)
        )

        pre_lesson_result = cursor.fetchone()

        if pre_lesson_result is None:
            print("Error: lesson cannot be found.")
            return

        (
            student_id,
            pre_subject_id,
            pre_lesson_state
        ) = pre_lesson_result

        if new_subject_id is None:
            new_subject_id = pre_subject_id

        if pre_lesson_state != "scheduled":
            print(
                f"Error: lesson cannot be rescheduled because its state is {pre_lesson_state}"
            )
            return

        # ----------------------------
        # Student conflict
        # ----------------------------
        
        cursor.execute(
            """
            SELECT 1
            FROM lessons
            WHERE student_id = ?
                AND lesson_date = ?
                AND time_slot_id = ?
                AND lesson_state IN (
                    'scheduled',
                    'completed'
                )
                AND lesson_id != ?
            LIMIT 1
            """,
            (
                student_id,
                new_lesson_date,
                new_time_slot_id,
                pre_lesson_id
            )
        )

        student_conflict_result = cursor.fetchone()

        if student_conflict_result is not None:
            print(
                "Error: Lesson for this student is already scheduled."
            )
            return

        # ----------------------------
        # Student conflict
        # ----------------------------

        if new_instructor_id is not None:
            cursor.execute(
                """
                SELECT 1
                FROM lessons
                WHERE instructor_id = ?
                    AND lesson_date = ?
                    AND time_slot_id = ?
                    AND lesson_state IN (
                        'scheduled',
                        'completed'
                    )
                    AND lesson_id != ?
                LIMIT 1
                """,
                (
                    new_instructor_id,
                    new_lesson_date,
                    new_time_slot_id,
                    pre_lesson_id
                )
            )

            instructor_conflict_result = cursor.fetchone()

            if instructor_conflict_result is not None:
                print("Error: Lesson for this instructor is already scheduled.")
                return

        # ----------------------------
        # Old lesson
        # ----------------------------

        cursor.execute(
            """
            UPDATE lessons
            SET lesson_state = ?
            WHERE lesson_id = ?
            """,
            (
                "rescheduled",
                pre_lesson_id
            )
        )
        # ----------------------------
        # New lesson
        # ----------------------------

        cursor.execute(
            """
            INSERT INTO lessons (
                student_id,
                instructor_id,
                subject_id,
                time_slot_id,
                lesson_date,
                lesson_state,
                rescheduled_from_lesson_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                new_instructor_id,
                new_subject_id,
                new_time_slot_id,
                new_lesson_date,
                "scheduled",
                pre_lesson_id
            )
        )

        connection.commit()

    except sqlite3.Error as e:
        connection.rollback()
        print(f"Database Error: {e}")

    finally:
        connection.close()
