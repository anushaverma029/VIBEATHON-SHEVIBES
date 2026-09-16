from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db


app = Flask(__name__)
CORS(app)


# =========================================================
# HOME
# =========================================================
@app.route("/", methods=["GET"])
def home():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_frontend(filename):
    return send_from_directory(".", filename)


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    course = data.get("course")
    year = data.get("year")
    interests = data.get("interests", "")

    if not name or not email or not password:

        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 6:

        return jsonify({
            "error": "Password must contain at least 6 characters"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        connection.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users
        (name, email, password, course, year, interests)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        hashed_password,
        course,
        year,
        interests
    ))

    user_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "course": course,
            "year": year,
            "interests": interests
        }
    }), 201


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    email = data.get("email")
    password = data.get("password")
    role = "admin" if "edu.in" in email.lower() else "student"
    if not email or not password:

        print("EMAIL:", email)
        print("ROLE:", role)
        return jsonify({
            "error": "Email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user is None:

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not check_password_hash(user["password"], password):

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "course": user["course"],
            "year": user["year"],
            "interests": user["interests"],
            "role": role
        }
    })

@app.route("/api/change-admin-password", methods=["POST"])
def change_admin_password():

    connection = get_db_connection()
    cursor = connection.cursor()

    hashed_password = generate_password_hash("admin123")

    cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE email = ?
    """, (
        hashed_password,
        "demo@campus.edu.in"
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Admin password updated successfully"
    })


# =========================================================
# GET USER PROFILE
# =========================================================

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, course, year, interests, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    connection.close()

    if user is None:

        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(dict(user))


# =========================================================
# UPDATE USER PROFILE
# =========================================================

@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "error": "User not found"
        }), 404

    name = data.get("name")
    course = data.get("course")
    year = data.get("year")
    interests = data.get("interests")

    cursor.execute("""
        UPDATE users
        SET
            name = COALESCE(?, name),
            course = COALESCE(?, course),
            year = COALESCE(?, year),
            interests = COALESCE(?, interests)
        WHERE id = ?
    """, (
        name,
        course,
        year,
        interests,
        user_id
    ))

    connection.commit()

    cursor.execute("""
        SELECT id, name, email, course, year, interests
        FROM users
        WHERE id = ?
    """, (user_id,))

    updated_user = cursor.fetchone()

    connection.close()

    return jsonify({
        "message": "Profile updated successfully",
        "user": dict(updated_user)
    })


# =========================================================
# CREATE NOTICE
# =========================================================

@app.route("/api/notices", methods=["POST"])
def create_notice():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    title = data.get("title")
    content = data.get("content")
    category = data.get("category", "General")
    target_course = data.get("target_course")
    target_year = data.get("target_year")
    is_important = data.get("is_important", 0)
    source = data.get("source")

    if not title or not content:

        return jsonify({
            "error": "Title and content are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

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
    """, (
        title,
        content,
        category,
        target_course,
        target_year,
        is_important,
        source
    ))

    notice_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO notice_versions
        (notice_id, version, title, content)
        VALUES (?, ?, ?, ?)
    """, (
        notice_id,
        1,
        title,
        content
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Notice created successfully",
        "notice_id": notice_id
    }), 201


# =========================================================
# GET ALL NOTICES
# =========================================================

@app.route("/api/notices", methods=["GET"])
def get_notices():

    category = request.args.get("category")
    search = request.args.get("search")

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT *
        FROM notices
        WHERE 1 = 1
    """

    parameters = []

    if category:

        query += " AND category = ?"
        parameters.append(category)

    if search:

        query += """
            AND (
                title LIKE ?
                OR content LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.append(search_value)
        parameters.append(search_value)

    query += """
        ORDER BY
            is_important DESC,
            created_at DESC
    """

    cursor.execute(query, parameters)

    notices = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(notice)
        for notice in notices
    ])


# =========================================================
# GET SINGLE NOTICE
# =========================================================

@app.route("/api/notices/<int:notice_id>", methods=["GET"])
def get_notice(notice_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM notices
        WHERE id = ?
    """, (notice_id,))

    notice = cursor.fetchone()

    connection.close()

    if notice is None:

        return jsonify({
            "error": "Notice not found"
        }), 404

    return jsonify(dict(notice))


# =========================================================
# UPDATE NOTICE
# =========================================================

@app.route("/api/notices/<int:notice_id>", methods=["PUT"])
def update_notice(notice_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM notices
        WHERE id = ?
    """, (notice_id,))

    old_notice = cursor.fetchone()

    if old_notice is None:

        connection.close()

        return jsonify({
            "error": "Notice not found"
        }), 404

    title = data.get("title", old_notice["title"])
    content = data.get("content", old_notice["content"])
    category = data.get("category", old_notice["category"])
    target_course = data.get(
        "target_course",
        old_notice["target_course"]
    )
    target_year = data.get(
        "target_year",
        old_notice["target_year"]
    )
    is_important = data.get(
        "is_important",
        old_notice["is_important"]
    )
    source = data.get(
        "source",
        old_notice["source"]
    )

    new_version = old_notice["version"] + 1

    cursor.execute("""
        UPDATE notices
        SET
            title = ?,
            content = ?,
            category = ?,
            target_course = ?,
            target_year = ?,
            is_important = ?,
            source = ?,
            version = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        title,
        content,
        category,
        target_course,
        target_year,
        is_important,
        source,
        new_version,
        notice_id
    ))

    cursor.execute("""
        INSERT INTO notice_versions
        (notice_id, version, title, content)
        VALUES (?, ?, ?, ?)
    """, (
        notice_id,
        new_version,
        title,
        content
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Notice updated successfully",
        "notice_id": notice_id,
        "version": new_version
    })


# =========================================================
# NOTICE HISTORY
# =========================================================

@app.route("/api/notices/<int:notice_id>/history", methods=["GET"])
def notice_history(notice_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM notice_versions
        WHERE notice_id = ?
        ORDER BY version DESC
    """, (notice_id,))

    versions = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(version)
        for version in versions
    ])


# =========================================================
# PERSONALIZED NOTICES
# =========================================================

@app.route("/api/users/<int:user_id>/notices", methods=["GET"])
def personalized_notices(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT course, year, interests
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "error": "User not found"
        }), 404

    course = user["course"]
    year = user["year"]
    interests = user["interests"] or ""

    cursor.execute("""
        SELECT *
        FROM notices
        WHERE
            (
                target_course IS NULL
                OR target_course = ?
            )
            AND
            (
                target_year IS NULL
                OR target_year = ?
            )
        ORDER BY
            is_important DESC,
            created_at DESC
    """, (
        course,
        year
    ))

    notices = cursor.fetchall()

    connection.close()

    result = []

    for notice in notices:

        notice_data = dict(notice)

        score = 0

        title_content = (
            notice["title"] + " " + notice["content"]
        ).lower()

        if interests:

            interest_list = [
                item.strip().lower()
                for item in interests.split(",")
            ]

            for interest in interest_list:

                if interest and interest in title_content:
                    score += 2

        if notice["target_course"] == course:
            score += 3

        if notice["target_year"] == year:
            score += 3

        if notice["is_important"]:
            score += 2

        notice_data["relevance_score"] = score

        result.append(notice_data)

    result.sort(
        key=lambda x: (
            x["relevance_score"],
            x["is_important"],
            x["created_at"]
        ),
        reverse=True
    )

    return jsonify(result)


# =========================================================
# CREATE EVENT
# =========================================================

@app.route("/api/events", methods=["POST"])
def create_event():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    title = data.get("title")
    description = data.get("description")
    category = data.get("category")
    venue = data.get("venue")
    event_date = data.get("event_date")
    registration_link = data.get("registration_link")
    target_course = data.get("target_course")
    target_year = data.get("target_year")

    if not title or not event_date:

        return jsonify({
            "error": "Title and event date are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

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
    """, (
        title,
        description,
        category,
        venue,
        event_date,
        registration_link,
        target_course,
        target_year
    ))

    event_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Event created successfully",
        "event_id": event_id
    }), 201


# =========================================================
# GET EVENTS
# =========================================================

@app.route("/api/events", methods=["GET"])
def get_events():

    category = request.args.get("category")
    search = request.args.get("search")

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT *
        FROM events
        WHERE 1 = 1
    """

    parameters = []

    if category:

        query += " AND category = ?"
        parameters.append(category)

    if search:

        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.append(search_value)
        parameters.append(search_value)

    query += " ORDER BY event_date ASC"

    cursor.execute(query, parameters)

    events = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(event)
        for event in events
    ])


# =========================================================
# PERSONALIZED EVENTS
# =========================================================

@app.route("/api/users/<int:user_id>/events", methods=["GET"])
def personalized_events(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT course, year
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "error": "User not found"
        }), 404

    cursor.execute("""
        SELECT *
        FROM events
        WHERE
            (
                target_course IS NULL
                OR target_course = ?
            )
            AND
            (
                target_year IS NULL
                OR target_year = ?
            )
        ORDER BY event_date ASC
    """, (
        user["course"],
        user["year"]
    ))

    events = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(event)
        for event in events
    ])


# =========================================================
# FEEDBACK
# =========================================================

@app.route("/api/feedback", methods=["POST"])
def create_feedback():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    user_id = data.get("user_id")
    notice_id = data.get("notice_id")
    event_id = data.get("event_id")
    feedback_type = data.get("feedback_type")

    if not user_id or not feedback_type:

        return jsonify({
            "error": "user_id and feedback_type are required"
        }), 400

    allowed_feedback = [
        "useful",
        "not_useful",
        "interested",
        "not_interested",
        "opened"
    ]

    if feedback_type not in allowed_feedback:

        return jsonify({
            "error": "Invalid feedback type"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO feedback
        (
            user_id,
            notice_id,
            event_id,
            feedback_type
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        notice_id,
        event_id,
        feedback_type
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Feedback recorded successfully"
    }), 201


# =========================================================
# USER FEEDBACK
# =========================================================

@app.route("/api/users/<int:user_id>/feedback", methods=["GET"])
def get_user_feedback(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM feedback
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    feedback = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(item)
        for item in feedback
    ])


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/api/users/<int:user_id>/dashboard", methods=["GET"])
def dashboard(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    # USER
    cursor.execute("""
        SELECT id, name, email, course, year, interests
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "error": "User not found"
        }), 404

    # NOTICES
    cursor.execute("""
        SELECT *
        FROM notices
        WHERE
            (
                target_course IS NULL
                OR target_course = ?
            )
            AND
            (
                target_year IS NULL
                OR target_year = ?
            )
        ORDER BY
            is_important DESC,
            created_at DESC
        LIMIT 10
    """, (
        user["course"],
        user["year"]
    ))

    notices = cursor.fetchall()

    # EVENTS
    cursor.execute("""
        SELECT *
        FROM events
        WHERE
            (
                target_course IS NULL
                OR target_course = ?
            )
            AND
            (
                target_year IS NULL
                OR target_year = ?
            )
        ORDER BY event_date ASC
        LIMIT 10
    """, (
        user["course"],
        user["year"]
    ))

    events = cursor.fetchall()

    # IMPORTANT NOTICES COUNT
    cursor.execute("""
        SELECT COUNT(*)
        FROM notices
        WHERE is_important = 1
    """)

    important_count = cursor.fetchone()[0]

    # FEEDBACK COUNT
    cursor.execute("""
        SELECT COUNT(*)
        FROM feedback
        WHERE user_id = ?
    """, (user_id,))

    feedback_count = cursor.fetchone()[0]

    connection.close()

    return jsonify({

        "user": dict(user),

        "statistics": {
            "important_notices": important_count,
            "feedback_given": feedback_count,
            "upcoming_events": len(events)
        },

        "notices": [
            dict(notice)
            for notice in notices
        ],

        "events": [
            dict(event)
            for event in events
        ]
    })


# =========================================================
# SEARCH
# =========================================================

@app.route("/api/search", methods=["GET"])
def search():

    query = request.args.get("q")

    if not query:

        return jsonify({
            "error": "Search query is required"
        }), 400

    search_value = f"%{query}%"

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            content,
            category,
            created_at,
            'notice' AS type
        FROM notices
        WHERE
            title LIKE ?
            OR content LIKE ?

        UNION ALL

        SELECT
            id,
            title,
            description AS content,
            category,
            created_at,
            'event' AS type
        FROM events
        WHERE
            title LIKE ?
            OR description LIKE ?

        ORDER BY created_at DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value
    ))

    results = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(result)
        for result in results
    ])


# =========================================================
# DATABASE STATUS
# =========================================================

@app.route("/api/status", methods=["GET"])
def status():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notices")
    notices = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM events")
    events = cursor.fetchone()[0]

    connection.close()

    return jsonify({
        "backend": "running",
        "database": "SQLite",
        "users": users,
        "notices": notices,
        "events": events
    })


# =========================================================
# START SERVER
# =========================================================

# =========================================================
# CAMPUSRADAR - NOTICE CHANGES
# =========================================================

@app.route("/api/notices/<int:notice_id>/changes", methods=["GET"])
def notice_changes(notice_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM notice_versions
        WHERE notice_id = ?
        ORDER BY version ASC
    """, (notice_id,))

    versions = cursor.fetchall()

    connection.close()

    if not versions:
        return jsonify({
            "error": "Notice not found"
        }), 404

    versions = [dict(version) for version in versions]

    if len(versions) == 1:
        return jsonify({
            "notice_id": notice_id,
            "changed": False,
            "current_version": versions[0]["version"],
            "previous_version": None,
            "message": "No changes detected yet"
        })

    previous = versions[-2]
    current = versions[-1]

    changes = []

    if previous["title"] != current["title"]:
        changes.append("Title changed")

    if previous["content"] != current["content"]:
        changes.append("Content changed")

    return jsonify({
        "notice_id": notice_id,
        "changed": len(changes) > 0,
        "previous_version": previous["version"],
        "current_version": current["version"],
        "changes": changes,
        "previous": {
            "title": previous["title"],
            "content": previous["content"]
        },
        "current": {
            "title": current["title"],
            "content": current["content"]
        }
    })

# =========================================================
# CAMPUSCUE - SMART NOTICE RELEVANCE
# =========================================================

@app.route("/api/users/<int:user_id>/smart-notices", methods=["GET"])
def smart_notices(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get user
    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        return jsonify({"error": "User not found"}), 404

    user = dict(user)

    # Get all notices
    cursor.execute("""
        SELECT *
        FROM notices
        ORDER BY created_at DESC
    """)

    notices = cursor.fetchall()
    connection.close()

    user_course = (user["course"] or "").lower()
    user_year = str(user["year"] or "").lower()

    interests = [
        interest.strip().lower()
        for interest in (user["interests"] or "").split(",")
    ]

    smart_results = []

    for notice in notices:

        notice = dict(notice)

        score = 0
        reasons = []

        # Course matching
        if notice["target_course"]:
            if notice["target_course"].lower() == user_course:
                score += 30
                reasons.append("Matches your course")
        else:
            score += 10
            reasons.append("Relevant to all students")

        # Year matching
        if notice["target_year"] is not None:
            if str(notice["target_year"]).lower() == user_year:
                score += 25
                reasons.append("Matches your year")
        else:
            score += 10

        # Important notice
        if notice["is_important"]:
            score += 20
            reasons.append("Marked as important")

        # Interest matching
        text = (
            (notice["title"] or "") + " " +
            (notice["content"] or "") + " " +
            (notice["category"] or "")
        ).lower()

        matched_interests = []

        for interest in interests:
            if interest and interest in text:
                score += 10
                matched_interests.append(interest)

        if matched_interests:
            reasons.append(
                "Matches your interests: "
                + ", ".join(matched_interests)
            )

        # Maximum score
        score = min(score, 100)

        # Relevance level
        if score >= 70:
            relevance = "Highly Relevant"
        elif score >= 40:
            relevance = "Relevant"
        else:
            relevance = "General"

        smart_results.append({
            "notice": notice,
            "relevance_score": score,
            "relevance": relevance,
            "reasons": reasons
        })

    # Highest relevance first
    smart_results.sort(
        key=lambda x: x["relevance_score"],
        reverse=True
    )

    return jsonify({
        "user": {
            "id": user["id"],
            "name": user["name"],
            "course": user["course"],
            "year": user["year"],
            "interests": user["interests"]
        },
        "smart_notices": smart_results
    })

# =========================================================
# CAMPUSCUE + CAMPUSRADAR SMART UPDATE
# =========================================================

@app.route("/api/users/<int:user_id>/notice-updates/<int:notice_id>", methods=["GET"])
def smart_notice_update(user_id, notice_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get user
    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        return jsonify({"error": "User not found"}), 404

    user = dict(user)

    # Get current notice
    cursor.execute(
        "SELECT * FROM notices WHERE id = ?",
        (notice_id,)
    )

    notice = cursor.fetchone()

    if not notice:
        connection.close()
        return jsonify({"error": "Notice not found"}), 404

    notice = dict(notice)

    # Get notice versions
    cursor.execute("""
        SELECT *
        FROM notice_versions
        WHERE notice_id = ?
        ORDER BY version ASC
    """, (notice_id,))

    versions = cursor.fetchall()

    connection.close()

    if len(versions) < 2:
        return jsonify({
            "notice_id": notice_id,
            "changed": False,
            "message": "No changes detected yet"
        })

    versions = [dict(v) for v in versions]

    previous = versions[-2]
    current = versions[-1]

    # Detect changes
    changes = []

    if previous["title"] != current["title"]:
        changes.append("Title changed")

    if previous["content"] != current["content"]:
        changes.append("Content changed")

    # Calculate relevance using CURRENT notice
    score = 0
    reasons = []

    # Course matching
    if notice["target_course"]:
        if notice["target_course"].lower() == user["course"].lower():
            score += 30
            reasons.append("Matches your course")
    else:
        score += 10
        reasons.append("Relevant to all students")

    # Year matching
    if notice["target_year"] is not None:
        if str(notice["target_year"]) == str(user["year"]):
            score += 25
            reasons.append("Matches your year")
    else:
        score += 10

    # Important notice
    if notice["is_important"]:
        score += 20
        reasons.append("Marked as important")

    # Interest matching
    interests = [
        i.strip().lower()
        for i in (user["interests"] or "").split(",")
    ]

    notice_text = (
        (notice["title"] or "") + " " +
        (notice["content"] or "") + " " +
        (notice["category"] or "")
    ).lower()

    matched_interests = []

    for interest in interests:
        if interest and interest in notice_text:
            score += 10
            matched_interests.append(interest)

    if matched_interests:
        reasons.append(
            "Matches your interests: "
            + ", ".join(matched_interests)
        )

    score = min(score, 100)

    if score >= 70:
        relevance = "Highly Relevant"
    elif score >= 40:
        relevance = "Relevant"
    else:
        relevance = "General"

    return jsonify({
        "changed": len(changes) > 0,
        "notice_id": notice_id,

        "previous_version": previous["version"],
        "current_version": current["version"],

        "changes": changes,

        "relevance": {
            "score": score,
            "level": relevance,
            "reasons": reasons
        },

        "previous": {
            "title": previous["title"],
            "content": previous["content"]
        },

        "current": {
            "title": current["title"],
            "content": current["content"]
        }
    })

# =========================================================
# CAMPUSCUE - STUDENT ALERTS
# =========================================================

@app.route("/api/users/<int:user_id>/alerts", methods=["GET"])
def student_alerts(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        return jsonify({"error": "User not found"}), 404

    user = dict(user)

    cursor.execute("""
        SELECT *
        FROM notices
        WHERE is_important = 1
        ORDER BY updated_at DESC
    """)

    notices = cursor.fetchall()
    connection.close()

    alerts = []

    for notice in notices:
        notice = dict(notice)

        alerts.append({
            "notice_id": notice["id"],
            "title": notice["title"],
            "content": notice["content"],
            "category": notice["category"],
            "source": notice["source"],
            "updated_at": notice["updated_at"],
            "alert": True
        })

    return jsonify({
        "user_id": user_id,
        "alerts": alerts,
        "count": len(alerts)
    })
if __name__ == "__main__":
    import os

    init_db()

    print("---------------------------------------")
    print("       CampusCue Backend")
    print("---------------------------------------")
    print("Database: SQLite")
    print("Server: http://127.0.0.1:5000")
    print("---------------------------------------")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
