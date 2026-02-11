from django.core.management.base import BaseCommand
from django.utils import timezone
from wizard.models import PinIdea
from wizard.services.pinterest_automation import PinterestAutomationService
import time

class Command(BaseCommand):
    help = 'Publishes scheduled pins that are due'

    def handle(self, *args, **options):
        self.stdout.write("Checking for scheduled pins...")
        
        # Find pins that are scheduled and due
        now = timezone.now()
        due_pins = PinIdea.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        
        count = due_pins.count()
        if count == 0:
            self.stdout.write("No pins due for publishing.")
            return

        self.stdout.write(f"Found {count} pins due. Starting publish...")
        
        service = PinterestAutomationService()
        success_count = 0
        
        for pin in due_pins:
            self.stdout.write(f"Publishing pin {pin.id}: {pin.title}...")
            try:
                pinterest_url = service.post_pin(
                    image_url=pin.image_url,
                    title=pin.title,
                    description=pin.description
                )
                
                pin.pinterest_url = pinterest_url or ''
                pin.posted_at = timezone.now()
                pin.status = 'posted'
                pin.save()
                
                self.stdout.write(self.style.SUCCESS(f"✓ Posted pin {pin.id}"))
                success_count += 1
                
                # Sleep briefly to avoid rate limits/issues
                time.sleep(5)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to post pin {pin.id}: {e}"))
                pin.status = 'failed'
                pin.save()
        
        self.stdout.write(self.style.SUCCESS(f"Finished. Successfully posted {success_count}/{count} pins."))
