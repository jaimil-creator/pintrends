import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pintrends_project.settings')
django.setup()

from wizard.models import BlogPost

posts = BlogPost.objects.all()
print(f"\n{'='*60}")
print(f"Total BlogPost records: {posts.count()}")
print(f"{'='*60}\n")

for post in posts:
    print(f"Blog ID: {post.id}")
    print(f"Topic: {post.topic}")
    print(f"Status: {post.generation_status}")
    print(f"Created: {post.created_at}")
    if post.error_message:
        print(f"Error: {post.error_message[:200]}")
    print(f"Intro length: {len(post.intro)} chars")
    print(f"Sections: {post.sections.count()}")
    print(f"{'-'*60}\n")

if posts.count() == 0:
    print("No blog posts found in database.")
