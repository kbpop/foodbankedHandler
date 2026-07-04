import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


load_dotenv()

def connect_to_db():
    try:
        # Establish the connection
        connection = mysql.connector.connect(
            host="mysql_container",
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