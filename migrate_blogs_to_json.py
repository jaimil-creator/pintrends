import os
import django
import json
import uuid
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pintrends_project.settings')
django.setup()

from wizard.models import BlogPost

def migrate_blogs():
    blogs = BlogPost.objects.all()
    print(f"Found {blogs.count()} blogs to migrate.")
    
    for blog in blogs:
        print(f"Migrating blog: {blog.topic}")
        
        # Construct JSON structure
        # Matches strict user requirement: title -> image_url -> button_text -> button_url -> description -> order
        features = []
        for section in blog.sections.all().order_by('order'):
            feature = {
                "title": section.title,
                "image_url": section.image_url,
                "button_text": "Try Now",
                "button_url": "https://www.dressr.ai/clothes-swap",
                "description": [section.description],
                # "order" is implicitly the index, but user asked for explicit ordering in description? 
                # The user request said: "title -> image url-> button-> description->order"
                # I will add "order" key at the end to be safe and explicit.
                "order": section.order 
            }
            features.append(feature)
        
        json_data = {
            "id": f"pinterest-blog-{uuid.uuid4().hex[:8]}",
            "title": blog.topic,
            "thumbnail_url": blog.thumbnail_url,
            "alt": f"{blog.topic} thumbnail",
            "description": [blog.intro],
            "metadata": {
                "title": blog.topic,
                "description": [blog.intro]
            },
            "features": features,
            "conclusion": [blog.conclusion],
            "publish_button_text": "Publish"
        }
        
        blog.structured_content = json_data
        blog.save()
        print(f"  -> Saved structured_content for blog {blog.id}")

    print("Migration complete!")

if __name__ == '__main__':
    migrate_blogs()
