import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


load_dotenv()

def connect_to_db():
    try:
        # Establish the connection
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            database=os.getenv("MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD")
        )
        
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None


def get_user_by_email(db, email):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_or_create_organization(db, name, org_type):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id FROM organizations WHERE name = %s AND org_type = %s",
        (name, org_type),
    )
    organization = cursor.fetchone()
    if organization:
        cursor.close()
        return organization["id"]

    cursor.execute(
        "INSERT INTO organizations (name, org_type) VALUES (%s, %s)",
        (name, org_type),
    )
    db.commit()
    organization_id = cursor.lastrowid
    cursor.close()
    return organization_id


def create_user(db, email, password_hash, account_type, verification_status, organization_id):
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO users (email, password_hash, account_type, verification_status, organization_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (email, password_hash, account_type, verification_status, organization_id),
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def list_pending_users(db):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT users.id, users.email, users.account_type, users.created_at,
               organizations.name AS organization_name, organizations.org_type
        FROM users
        LEFT JOIN organizations ON organizations.id = users.organization_id
        WHERE users.verification_status = 'pending'
        """
    )
    pending_users = cursor.fetchall()
    cursor.close()
    return pending_users


def set_verification_status(db, user_id, status):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET verification_status = %s WHERE id = %s",
        (status, user_id),
    )
    db.commit()
    cursor.close()
