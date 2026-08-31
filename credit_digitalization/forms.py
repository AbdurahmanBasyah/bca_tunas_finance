from django import forms
from django.core.exceptions import ValidationError

from .models import CreditApplication


class CreditApplicationForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024

    class Meta:
        model = CreditApplication
        fields = [
            'dealer_name', 'dealer_sales_name',
            'consumer_name', 'nik', 'phone_number', 'birth_date',
            'marital_status', 'spouse_name', 'consent_personal_data',
            'vehicle_brand', 'vehicle_model', 'vehicle_type',
            'vehicle_color', 'vehicle_price',
            'insurance_type', 'down_payment', 'tenor_months',
            'monthly_installment',
            'ktp_document', 'family_card_document',
            'booking_fee_document', 'application_form_document',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'vehicle_price': forms.NumberInput(attrs={'min': 0, 'step': 100000}),
            'down_payment': forms.NumberInput(attrs={'min': 0, 'step': 100000}),
            'monthly_installment': forms.NumberInput(attrs={'min': 0, 'step': 100000}),
            'tenor_months': forms.NumberInput(attrs={'min': 1, 'max': 120}),
            'consent_personal_data': forms.CheckboxInput(),
        }
        help_texts = {
            'consent_personal_data': (
                'Konsumen telah menerima penjelasan dan menyetujui pemrosesan '
                'data untuk pengajuan kredit.'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        for name in (
            'ktp_document', 'family_card_document',
            'booking_fee_document', 'application_form_document',
        ):
            self.fields[name].widget.attrs['accept'] = '.pdf,.jpg,.jpeg,.png'

    def clean_nik(self):
        nik = self.cleaned_data.get('nik', '').strip()
        if nik and (not nik.isdigit() or len(nik) != 16):
            raise ValidationError('NIK harus terdiri dari tepat 16 digit angka.')
        return nik

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('vehicle_price')
        down_payment = cleaned_data.get('down_payment')
        if price is not None and down_payment is not None and down_payment > price:
            self.add_error(
                'down_payment',
                'Down payment tidak boleh lebih besar dari harga kendaraan.',
            )
        for name in (
            'ktp_document', 'family_card_document',
            'booking_fee_document', 'application_form_document',
        ):
            uploaded_file = cleaned_data.get(name)
            if uploaded_file and uploaded_file.size > self.MAX_UPLOAD_SIZE:
                self.add_error(name, 'Ukuran file maksimal 5 MB.')
        return cleaned_data


class ReviewForm(forms.Form):
    DECISIONS = (
        (CreditApplication.Status.APPROVED, 'Setujui'),
        (CreditApplication.Status.REJECTED, 'Tolak'),
    )
    decision = forms.ChoiceField(choices=DECISIONS, widget=forms.HiddenInput())
    notes = forms.CharField(
        label='Catatan review',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Wajib diisi apabila pengajuan ditolak',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('decision') == CreditApplication.Status.REJECTED
            and not cleaned_data.get('notes', '').strip()
        ):
            self.add_error('notes', 'Alasan penolakan wajib diisi.')
        return cleaned_data
