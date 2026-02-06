from database.db import SessionLocal
from database.models import Suggestion, Keyword
from sqlalchemy import func

def check_duplicates():
    db = SessionLocal()
    try:
        # Find duplicates
        duplicates = db.query(
            Suggestion.parent_keyword_id,
            Suggestion.suggestion,
            func.count(Suggestion.id)
        ).group_by(
            Suggestion.parent_keyword_id,
            Suggestion.suggestion
        ).having(func.count(Suggestion.id) > 1).all()
        
        print(f"Found {len(duplicates)} duplicate groups.")
        for d in duplicates[:5]:
            kw = db.query(Keyword).get(d[0])
            print(f"Keyword: {kw.keyword if kw else 'Unknown'}, Suggestion: {d[1]}, Count: {d[2]}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_duplicates()
