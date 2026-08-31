from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .apps import CreditDigitalizationConfig


@receiver(post_migrate, sender=CreditDigitalizationConfig)
def create_application_roles(**kwargs):
    Group.objects.get_or_create(name='Marketing')
    Group.objects.get_or_create(name='Atasan Marketing')
