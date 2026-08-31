import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def application_document_path(instance, filename):
    safe_filename = Path(filename).name
    return f'applications/{instance.created_by_id}/{uuid.uuid4().hex}/{safe_filename}'


document_validators = [
    FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
]


class CreditApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Diajukan'
        APPROVED = 'APPROVED', 'Disetujui'
        REJECTED = 'REJECTED', 'Ditolak'

    class MaritalStatus(models.TextChoices):
        SINGLE = 'SINGLE', 'Belum Menikah'
        MARRIED = 'MARRIED', 'Menikah'
        DIVORCED = 'DIVORCED', 'Cerai'

    class InsuranceType(models.TextChoices):
        ALL_RISK = 'ALL_RISK', 'All Risk'
        TLO = 'TLO', 'Total Loss Only (TLO)'
        COMBINATION = 'COMBINATION', 'Kombinasi'

    application_number = models.CharField(max_length=30, unique=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    # Lead/dealer data
    dealer_name = models.CharField('nama dealer', max_length=150, blank=True)
    dealer_sales_name = models.CharField('nama sales dealer', max_length=150, blank=True)

    # Customer data
    consumer_name = models.CharField('nama konsumen', max_length=150, blank=True)
    nik = models.CharField('NIK', max_length=16, blank=True)
    phone_number = models.CharField('nomor telepon', max_length=20, blank=True)
    birth_date = models.DateField('tanggal lahir', null=True, blank=True)
    marital_status = models.CharField(
        'status perkawinan',
        max_length=10,
        choices=MaritalStatus.choices,
        blank=True,
    )
    spouse_name = models.CharField('nama pasangan', max_length=150, blank=True)
    consent_personal_data = models.BooleanField(
        'persetujuan pemrosesan data pribadi',
        default=False,
    )
    consent_at = models.DateTimeField(
        'waktu persetujuan data pribadi', null=True, blank=True, editable=False
    )

    # Vehicle data
    vehicle_brand = models.CharField('merk kendaraan', max_length=100, blank=True)
    vehicle_model = models.CharField('model kendaraan', max_length=100, blank=True)
    vehicle_type = models.CharField('tipe kendaraan', max_length=100, blank=True)
    vehicle_color = models.CharField('warna kendaraan', max_length=50, blank=True)
    vehicle_price = models.DecimalField(
        'harga kendaraan',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Financing data
    insurance_type = models.CharField(
        'jenis asuransi',
        max_length=15,
        choices=InsuranceType.choices,
        blank=True,
    )
    down_payment = models.DecimalField(
        'down payment',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tenor_months = models.PositiveSmallIntegerField(
        'lama kredit (bulan)', null=True, blank=True
    )
    monthly_installment = models.DecimalField(
        'angsuran per bulan',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Uploaded requirements
    ktp_document = models.FileField(
        'KTP', upload_to=application_document_path, blank=True,
        validators=document_validators,
    )
    family_card_document = models.FileField(
        'kartu keluarga', upload_to=application_document_path, blank=True,
        validators=document_validators,
    )
    booking_fee_document = models.FileField(
        'bukti bayar tanda jadi', upload_to=application_document_path, blank=True,
        validators=document_validators,
    )
    application_form_document = models.FileField(
        'form aplikasi pengajuan', upload_to=application_document_path, blank=True,
        validators=document_validators,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_credit_applications',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reviewed_credit_applications',
        null=True,
        blank=True,
    )
    rejection_reason = models.TextField('alasan penolakan', blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'pengajuan kredit'
        verbose_name_plural = 'pengajuan kredit'

    def __str__(self):
        return f'{self.application_number} - {self.consumer_name or "Tanpa nama"}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.consent_personal_data and not self.consent_at:
            self.consent_at = timezone.now()
        elif not self.consent_personal_data:
            self.consent_at = None
        super().save(*args, **kwargs)
        if is_new and not self.application_number:
            number = f'APP-{timezone.localdate():%Y%m}-{self.pk:05d}'
            type(self).objects.filter(pk=self.pk).update(application_number=number)
            self.application_number = number

    @property
    def missing_requirements(self):
        required_fields = {
            'dealer_name': 'Nama dealer',
            'dealer_sales_name': 'Nama sales dealer',
            'consumer_name': 'Nama konsumen',
            'nik': 'NIK',
            'phone_number': 'Nomor telepon',
            'birth_date': 'Tanggal lahir',
            'marital_status': 'Status perkawinan',
            'vehicle_brand': 'Merk kendaraan',
            'vehicle_model': 'Model kendaraan',
            'vehicle_type': 'Tipe kendaraan',
            'vehicle_color': 'Warna kendaraan',
            'vehicle_price': 'Harga kendaraan',
            'insurance_type': 'Jenis asuransi',
            'down_payment': 'Down payment',
            'tenor_months': 'Lama kredit',
            'monthly_installment': 'Angsuran per bulan',
            'ktp_document': 'Dokumen KTP',
            'family_card_document': 'Dokumen kartu keluarga',
            'booking_fee_document': 'Bukti bayar tanda jadi',
            'application_form_document': 'Form aplikasi pengajuan',
        }
        missing = [
            label for field, label in required_fields.items()
            if getattr(self, field) in (None, '')
        ]
        if self.marital_status == self.MaritalStatus.MARRIED and not self.spouse_name:
            missing.append('Nama pasangan')
        if not self.consent_personal_data:
            missing.append('Persetujuan pemrosesan data pribadi')
        return missing

    @property
    def is_complete(self):
        return not self.missing_requirements

    @property
    def status_badge_class(self):
        return {
            self.Status.DRAFT: 'bg-secondary',
            self.Status.SUBMITTED: 'bg-warning text-dark',
            self.Status.APPROVED: 'bg-success',
            self.Status.REJECTED: 'bg-danger',
        }[self.status]


class ApplicationAuditTrail(models.Model):
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Dibuat'
        UPDATED = 'UPDATED', 'Diperbarui'
        SUBMITTED = 'SUBMITTED', 'Diajukan'
        APPROVED = 'APPROVED', 'Disetujui'
        REJECTED = 'REJECTED', 'Ditolak'

    application = models.ForeignKey(
        CreditApplication,
        on_delete=models.CASCADE,
        related_name='audit_trails',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='credit_application_activities',
    )
    action = models.CharField(max_length=12, choices=Action.choices)
    from_status = models.CharField(max_length=12, blank=True)
    to_status = models.CharField(max_length=12)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'audit pengajuan'
        verbose_name_plural = 'audit pengajuan'

    def __str__(self):
        return f'{self.application.application_number} - {self.get_action_display()}'
