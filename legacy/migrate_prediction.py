from database.db import engine, Base
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(trend_keywords)"))
            columns = [row[1] for row in result]
            
            if "prediction_data" not in columns:
                print("Column 'prediction_data' not found. Adding...")
                conn.execute(text("ALTER TABLE trend_keywords ADD COLUMN prediction_data TEXT"))
                print("Column added successfully.")
            else:
                print("Column 'prediction_data' already exists.")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate()
