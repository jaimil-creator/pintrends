import os
import django
import sys

# Set up Django environment
sys.path.append('e:/Pintrends/pintrends')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pintrends_project.settings')
django.setup()

from wizard.services.pinterest_automation import PinterestAutomationService
from datetime import datetime, timedelta

service = PinterestAutomationService()

# Schedule for tomorrow
tomorrow = datetime.now() + timedelta(days=1)
schedule_date = tomorrow.strftime("%Y-%m-%d")
schedule_time = "02:30 PM"

print(f"Testing schedule for Date: {schedule_date}, Time: {schedule_time}")

try:
    result = service.post_pin(
        image_url="https://images.unsplash.com/photo-1575936123452-b67c3203c357?q=80&w=1000&auto=format&fit=crop",
        title="Test Scheduling Pin",
        description="This is a test pin for verifying scheduling automation.",
        link="https://example.com",
        board_name="clothing",
        schedule_date=schedule_date,
        schedule_time=schedule_time,
        tags="test, automation"
    )
    print("Result:", result)
except Exception as e:
    print("Error during test:", e)
