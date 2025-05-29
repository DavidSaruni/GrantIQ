from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create test users for each role'

    def handle(self, *args, **kwargs):
        roles = [
            ('admin@example.com', 'ADMIN'),
            ('manager@example.com', 'GRANT_MANAGER'),
            ('reviewer@example.com', 'REVIEWER'),
            ('applicant@example.com', 'APPLICANT'),
        ]

        for email, role in roles:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'role': role,
                    'is_active': True,
                    'is_staff': role in ['ADMIN', 'GRANT_MANAGER'],
                    'is_superuser': role == 'ADMIN'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created {role} user: {email}"))
            else:
                self.stdout.write(self.style.WARNING(f"{email} already exists"))
