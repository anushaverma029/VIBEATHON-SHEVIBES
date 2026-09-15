import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "campuscue.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            course TEXT,
            year INTEGER,
            interests TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # NOTICES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            target_course TEXT,
            target_year INTEGER,
            is_important INTEGER DEFAULT 0,
            source TEXT,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # NOTICE VERSIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notice_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (notice_id) REFERENCES notices(id) ON DELETE CASCADE
        )
    """)

    # EVENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            venue TEXT,
            event_date TEXT NOT NULL,
            registration_link TEXT,
            target_course TEXT,
            target_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FEEDBACK
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            notice_id INTEGER,
            event_id INTEGER,
            feedback_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (notice_id) REFERENCES notices(id) ON DELETE CASCADE,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    """)

    connection.commit()

    # --------------------------------------------------
    # SAMPLE USER
    # --------------------------------------------------

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        ("demo@campuscue.com",)
    )

    if cursor.fetchone() is None:
        hashed_password = generate_password_hash("demo123")

        cursor.execute("""
            INSERT INTO users
            (name, email, password, course, year, interests)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Demo Student",
            "demo@campuscue.com",
            hashed_password,
            "ECE",
            1,
            "AI,Robotics,Hackathons"
        ))

    # --------------------------------------------------
    # SAMPLE NOTICES
    # --------------------------------------------------

    cursor.execute("SELECT COUNT(*) FROM notices")
    notice_count = cursor.fetchone()[0]

    if notice_count == 0:

        notices = [

            (
                "ECE Department Orientation",
                "Orientation for first-year ECE students will be held in the main auditorium.",
                "Academic",
                "ECE",
                1,
                1,
                "ECE Department"
            ),

            (
                "Hackathon Registrations Open",
                "Registrations are now open for the upcoming college hackathon.",
                "Hackathon",
                None,
                None,
                1,
                "Innovation Cell"
            ),

            (
                "Library Timings Updated",
                "The library will remain open from 8:00 AM to 8:00 PM on weekdays.",
                "General",
                None,
                None,
                0,
                "Central Library"
            ),

            (
                "AI Workshop",
                "A hands-on workshop on Artificial Intelligence and Machine Learning will be conducted this weekend.",
                "Workshop",
                "ECE",
                None,
                0,
                "Technical Club"
            )
        ]

        for notice in notices:

            cursor.execute("""
                INSERT INTO notices
                (
                    title,
                    content,
                    category,
                    target_course,
                    target_year,
                    is_important,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, notice)

            notice_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO notice_versions
                (notice_id, version, title, content)
                VALUES (?, ?, ?, ?)
            """, (
                notice_id,
                1,
                notice[0],
                notice[1]
            ))

    # --------------------------------------------------
    # SAMPLE EVENTS
    # --------------------------------------------------

    cursor.execute("SELECT COUNT(*) FROM events")
    event_count = cursor.fetchone()[0]

    if event_count == 0:

        events = [

            (
                "Campus Hackathon",
                "24-hour coding and innovation hackathon.",
                "Hackathon",
                "Innovation Lab",
                "2026-10-10 09:00",
                "https://example.com/register",
                None,
                None
            ),

            (
                "AI & Machine Learning Workshop",
                "Beginner-friendly workshop covering AI and ML fundamentals.",
                "Workshop",
                "Seminar Hall",
                "2026-09-25 14:00",
                "https://example.com/ai-workshop",
                "ECE",
                None
            ),

            (
                "Freshers Technical Meetup",
                "An introductory meetup for first-year students interested in technology.",
                "Meetup",
                "Auditorium",
                "2026-09-20 11:00",
                "https://example.com/meetup",
                None,
                1
            )
        ]

        for event in events:

            cursor.execute("""
                INSERT INTO events
                (
                    title,
                    description,
                    category,
                    venue,
                    event_date,
                    registration_link,
                    target_course,
                    target_year
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, event)

    connection.commit()
    connection.close()