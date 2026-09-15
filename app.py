import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)  # allows your Vercel frontend (a different domain) to call this API

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_ai(prompt):
    """Calls a hosted LLM instead of a local Ollama server (which won't
    exist once this app is deployed to Render/Railway/etc.)."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def get_db_connection():
    """Reads DB credentials from environment variables instead of
    hardcoding localhost — set these in your host's dashboard
    (Render/Railway) after creating a cloud MySQL database."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


@app.route("/")
def home():
    return "CampusCue backend is running!"


@app.route("/test-db")
def test_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return f"Connected to database: {result[0]}"


@app.route("/announcements", methods=["POST"])
def add_announcement():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    category = data.get("category")
    priority = data.get("priority", "normal")
    target_audience = data.get("target_audience")
    event_date = data.get("event_date")
    source = data.get("source")

    if not title or not description:
        return jsonify({"error": "Title and description are required"}), 400

    ai_text = ask_ai(f"""
Analyze this campus announcement.
Title: {title}
Description: {description}

Return ONLY in this exact format:
Summary: <short student-friendly summary>
Category: <category>
Priority: <low, normal, or high>
Target Audience: <who should care about this announcement>

Do not add anything else.
""")

    ai_summary = ""
    ai_category = ""
    ai_priority = ""
    ai_target_audience = ""
    for line in ai_text.splitlines():
        if line.startswith("Summary:"):
            ai_summary = line.replace("Summary:", "").strip()
        elif line.startswith("Category:"):
            ai_category = line.replace("Category:", "").strip()
        elif line.startswith("Priority:"):
            ai_priority = line.replace("Priority:", "").strip()
        elif line.startswith("Target Audience:"):
            ai_target_audience = line.replace("Target Audience:", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO announcements
        (title, description, category, priority,
         target_audience, event_date, source,
         ai_summary, ai_category, ai_priority, ai_target_audience)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        title, description, category, priority,
        target_audience, event_date, source,
        ai_summary, ai_category, ai_priority, ai_target_audience,
    )
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Announcement added successfully!"}), 201


@app.route("/announcements", methods=["GET"])
def get_announcements():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM announcements
        ORDER BY created_at DESC
    """)
    announcements = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(announcements)


@app.route("/my-announcements/<int:user_id>", methods=["GET"])
def get_my_announcements(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT announcements.*
        FROM announcements
        JOIN users ON users.id = %s
        WHERE
            announcements.target_audience = 'All Students'
            OR announcements.target_audience = users.course
            OR announcements.target_audience = CONCAT('Year ', users.year)
        ORDER BY announcements.created_at DESC
    """, (user_id,))
    announcements = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(announcements)


# NOTE: this was previously stacked onto get_my_announcements by mistake,
# which meant POST /register would crash. It now has its own route.
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    course = data.get("course")
    year = data.get("year")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO users (name, email, password, course, year)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (name, email, password, course, year)
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "User registered successfully!"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, email, password, course, year
        FROM users WHERE email = %s
    """, (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user or user["password"] != password:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful!",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "course": user["course"],
            "year": user["year"],
        },
    }), 200


@app.route("/ai-test", methods=["POST"])
def ai_test():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"error": "Text is required"}), 400
    ai_response = ask_ai(f"Understand this campus announcement and summarize it for a student:\n{text}")
    return jsonify({"ai_response": ai_response})


@app.route("/detect-change", methods=["POST"])
def detect_change():
    data = request.get_json()
    old_text = data.get("old_text")
    new_text = data.get("new_text")

    if not old_text or not new_text:
        return jsonify({"error": "Both old_text and new_text are required"}), 400

    ai_response = ask_ai(f"""
Compare these two campus announcements.

OLD ANNOUNCEMENT:
{old_text}

NEW ANNOUNCEMENT:
{new_text}

Tell me:
1. Whether anything changed
2. What changed
3. Whether the change is important for students

Return a short, clear response.
""")
    return jsonify({"change_analysis": ai_response})


@app.route("/alerts/<int:announcement_id>", methods=["GET"])
def get_alert(announcement_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT title, ai_summary, ai_priority
        FROM announcements WHERE id = %s
    """, (announcement_id,))
    announcement = cursor.fetchone()
    cursor.close()
    connection.close()

    if not announcement:
        return jsonify({"error": "Announcement not found"}), 404

    if announcement["ai_priority"].lower() == "high":
        return jsonify({
            "alert": True,
            "message": "Important CampusCue Update",
            "title": announcement["title"],
            "summary": announcement["ai_summary"],
        })

    return jsonify({"alert": False, "message": "No urgent alert for this announcement."})


if __name__ == "__main__":
    # Render/Railway set PORT via env var; 0.0.0.0 makes it reachable externally
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
