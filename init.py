import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "test.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                school_level TEXT NOT NULL,
                grade INTEGER NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS instructors (
                instructor_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS time_slots (
                time_slot_id INTEGER PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                instructor_id INTEGER,
                subject_id INTEGER NOT NULL,
                time_slot_id INTEGER NOT NULL,
                lesson_date TEXT NOT NULL,

                lesson_state TEXT NOT NULL
                    CHECK (
                        lesson_state IN (
                            'scheduled',
                            'completed',
                            'canceled',
                            'rescheduled'
                        )
                    ),
                
                rescheduled_from_lesson_id INTEGER,

                FOREIGN KEY (student_id)
                    REFERENCES students(student_id),
                
                FOREIGN KEY (instructor_id)
                    REFERENCES instructors(instructor_id),
                
                FOREIGN KEY (subject_id)
                    REFERENCES subjects(subject_id),

                FOREIGN KEY (time_slot_id)
                    REFERENCES time_slots(time_slot_id),
                
                FOREIGN KEY (rescheduled_from_lesson_id)
                    REFERENCES lessons(lesson_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_credit_transactions (
                transaction_id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                change_amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                lesson_id INTEGER,

                FOREIGN KEY (student_id)
                    REFERENCES students(student_id),
                
                FOREIGN KEY (lesson_id)
                    REFERENCES lessons(lesson_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_monthly_plans (
                student_id INTEGER NOT NULL,
                year INTEGER NOT NULL,

                month INTEGER NOT NULL
                    CHECK (month BETWEEN 1 AND 12),
                
                lessons_per_month INTEGER NOT NULL
                    CHECK (lessons_per_month >= 0),
                
                granted_at TEXT,

                PRIMARY KEY (student_id, year, month),

                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
            )
            """
        )

        # ----------------------------
        # Test data: students
        # ----------------------------

        cursor.executemany(
            """
            INSERT INTO students (
                student_id,
                name,
                school_level,
                grade
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, "Student 1", "high", 1),
                (2, "Student 2", "high", 1),
                (3, "Student 3", "high", 1),
                (4, "Student 4", "high", 1),
                (5, "Student 5", "high", 1),
            ]
        )

        # ----------------------------
        # Test data: monthly plans
        # ----------------------------

        cursor.executemany(
            """
            INSERT INTO student_monthly_plans (
                student_id,
                year,
                month,
                lessons_per_month,
                granted_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, 2026, 10, 4, None),
                (2, 2026, 11, 4, None),
                (3, 2025, 10, 4, None),
                (4, 2026, 10, 4, "2026-10-01T00:00:00"),
                (5, 2026, 10, 8, None),
            ]
        )

        # ----------------------------
        # Test data: instructors
        # ----------------------------

        cursor.executemany(
            """
            INSERT INTO instructors (
                instructor_id,
                name
            )
            VALUES (?, ?)
            """,
            [
                (1, "instructor_1"),
                (2, "instructor_2"),
            ]
        )

        # ----------------------------
        # Test data: subjects
        # ----------------------------

        cursor.executemany(
            """
            INSERT INTO subjects (
                subject_id,
                name
            )
            VALUES (?, ?)
            """,
            [
                (1, "Math"),
                (2, "English"),
            ]
        )

        # ----------------------------
        # Test data: time slot
        # ----------------------------

        cursor.execute(
            """
            INSERT INTO time_slots (
                time_slot_id,
                start_time,
                end_time
            )
            VALUES (?, ?, ?)
            """,
            (1, "11:40", "13:00")
        )

        # ----------------------------
        # Test data: lesson
        # ----------------------------

        cursor.execute(
            """
            INSERT INTO lessons (
                lesson_id,
                student_id,
                instructor_id,
                subject_id,
                time_slot_id,
                lesson_date,
                lesson_state
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                1,
                1,
                1,
                1,
                "2026-10-10",
                "scheduled"
            )
        )

        connection.commit()

    except sqlite3.Error as e:
        connection.rollback()
        print(f"Database initialization failed: {e}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
