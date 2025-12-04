import os
from dotenv import load_dotenv
import psycopg2

load_dotenv() 

db_url = os.getenv("DATABASE_URL")
print("Using:", db_url)

conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("SELECT 1;")
print("Result:", cur.fetchone())

cur.close()
conn.close()
print("OK, DB connection works.")