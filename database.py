import mysql.connector


def create_database():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )

    cursor = connection.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS campuscue_db")

    cursor.close()
    connection.close()

    print("CampusCue database created successfully!")


def create_users_table():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="campuscue_db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            course VARCHAR(100),
            year INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()

    print("Users table created successfully!")

def create_announcements_table():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="campuscue_db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100),
            priority VARCHAR(50) DEFAULT 'normal',
            target_audience VARCHAR(255),
            event_date DATE,
            source VARCHAR(255),
            ai_summary TEXT,
            ai_category VARCHAR(100),
            ai_priority VARCHAR(50),
            ai_target_audience VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()

    print("Announcements table created successfully!")    


if __name__ == "__main__":
    create_database()
    create_users_table()
    create_announcements_table()
    