import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

db_name = os.getenv('DB_NAME', 'mero_kharcha_db')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_host = os.getenv('DB_HOST', '127.0.0.1')
db_port = int(os.getenv('DB_PORT', '3306'))

try:
    # Connect to MySQL server (without specifying a database)
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        port=db_port
    )
    
    with connection.cursor() as cursor:
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created successfully (or already exists).")

    connection.close()

except pymysql.err.OperationalError as e:
    print(f"Error: Could not connect to MySQL server. Please make sure XAMPP/MySQL is running.")
    print(f"Original Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
