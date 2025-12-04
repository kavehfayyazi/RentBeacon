import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def show_tables():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            table_names = [name for (name,) in tables]

            print("Tables:")
            for name in table_names:
                print("  -", name)

            return table_names

def show_table_contents(table_name: str, limit: int = 50):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} LIMIT %s;", (limit,))
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]

            print(f"\n{table_name} (first {limit} rows):")
            print(" | ".join(colnames))
            print("-" * 40)
            for row in rows:
                print(" | ".join(str(v) for v in row))

if __name__ == "__main__":
    tables = show_tables()

    if "listings" in tables:
        show_table_contents("listings")
    else:
        print('\n[inspect_db] Table "listings" does not exist in this database.')
        print("Make sure you’ve run rentcast_scraper.py to create it first.")