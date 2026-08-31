from django.apps import AppConfig


class CreditDigitalizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'credit_digitalization'
    verbose_name = 'Digitalisasi Kredit'

    def ready(self):
        from . import signals  # noqa: F401
