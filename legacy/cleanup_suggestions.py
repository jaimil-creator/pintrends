from database.db import SessionLocal
from database.models import Suggestion
from sqlalchemy import func

def cleanup_duplicates():
    db = SessionLocal()
    try:
        # Identify duplicates: group by parent and suggestion text
        print("Finding duplicates...")
        
        # We want to keep the one with the lowest ID (first inserted)
        # SQLite doesn't support complex DELETE JOINs nicely, so we'll fetch IDs to delete.
        
        subq = db.query(
            Suggestion.parent_keyword_id, 
            Suggestion.suggestion, 
            func.min(Suggestion.id).label("min_id")
        ).group_by(
            Suggestion.parent_keyword_id, 
            Suggestion.suggestion
        ).having(func.count(Suggestion.id) > 1).all()
        
        print(f"Found {len(subq)} groups with duplicates.")
        
        total_deleted = 0
        
        for parent_id, sugg_text, min_id in subq:
            # Find IDs to delete (same parent, same text, but ID != min_id)
            to_delete = db.query(Suggestion).filter(
                Suggestion.parent_keyword_id == parent_id,
                Suggestion.suggestion == sugg_text,
                Suggestion.id != min_id
            ).all()
            
            for item in to_delete:
                db.delete(item)
                total_deleted += 1
                
        db.commit()
        print(f"Cleanup complete. Deleted {total_deleted} duplicate records.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
