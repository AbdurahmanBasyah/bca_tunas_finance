from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from credit_digitalization.access import MARKETING_ROLE, SUPERVISOR_ROLE


class Command(BaseCommand):
    help = 'Membuat akun demo Marketing dan Atasan Marketing.'

    def handle(self, *args, **options):
        accounts = (
            ('marketing_demo', 'Marketing Demo', MARKETING_ROLE),
            ('supervisor_demo', 'Supervisor Demo', SUPERVISOR_ROLE),
        )
        for username, full_name, role in accounts:
            first_name, last_name = full_name.split(' ', 1)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'last_name': last_name},
            )
            if created:
                user.set_password('Demo12345!')
                user.save()
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            state = 'dibuat' if created else 'sudah tersedia'
            self.stdout.write(self.style.SUCCESS(
                f'{username} ({role}) {state}.'
            ))
        self.stdout.write('Password awal untuk akun baru: Demo12345!')
