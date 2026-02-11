from wizard.models import PinIdea
from django.utils import timezone

print(f"Current Time (timezone.now()): {timezone.now()}")

scheduled_pins = PinIdea.objects.filter(status='scheduled')
print(f"Total Scheduled Pins: {scheduled_pins.count()}")

for pin in scheduled_pins:
    print(f"Pin ID: {pin.id}")
    print(f"Title: {pin.title}")
    print(f"Scheduled At: {pin.scheduled_at}")
    print(f"Is Due? {pin.scheduled_at <= timezone.now() if pin.scheduled_at else 'No Date'}")
    print("-" * 20)
