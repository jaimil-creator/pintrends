from database.db import engine, Base
from database.models import TrendKeyword, Suggestion

print("Dropping tables...")
try:
    TrendKeyword.__table__.drop(engine)
    # Suggestion table doesn't need change but might as well restart clean to sync with fresh trends
    Suggestion.__table__.drop(engine)
    print("Tables dropped.")
except Exception as e:
    print(f"Error dropping: {e}")

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables recreated successfully with new columns.")
