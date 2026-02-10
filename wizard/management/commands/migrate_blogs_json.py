from django.core.management.base import BaseCommand
from wizard.models import BlogPost
import uuid
import json

class Command(BaseCommand):
    help = 'Migrates existing blog posts to the new structured_content JSON format'

    def handle(self, *args, **options):
        blogs = BlogPost.objects.all()
        self.stdout.write(f"Found {blogs.count()} blogs to migrate.")
        
        for blog in blogs:
            self.stdout.write(f"Migrating blog: {blog.topic}")
            
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
            self.stdout.write(self.style.SUCCESS(f"  -> Saved structured_content for blog {blog.id}"))

        self.stdout.write(self.style.SUCCESS("Migration complete!"))
