from pathlib import Path

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import (
    MARKETING_ROLE,
    SUPERVISOR_ROLE,
    get_role_label,
    has_role,
    role_required,
)
from .forms import CreditApplicationForm, ReviewForm
from .models import ApplicationAuditTrail, CreditApplication


def _visible_applications(user):
    applications = CreditApplication.objects.select_related(
        'created_by', 'reviewed_by'
    )
    if user.is_superuser:
        return applications
    if has_role(user, SUPERVISOR_ROLE):
        # Checker only receives data after it has been submitted. If a user has
        # both roles, their own draft remains visible but other makers' drafts do not.
        if has_role(user, MARKETING_ROLE):
            return applications.filter(
                Q(created_by=user) | ~Q(status=CreditApplication.Status.DRAFT)
            )
        return applications.exclude(status=CreditApplication.Status.DRAFT)
    if has_role(user, MARKETING_ROLE):
        return applications.filter(created_by=user)
    return applications.none()


def _get_visible_application(user, pk):
    return get_object_or_404(_visible_applications(user), pk=pk)


@role_required(MARKETING_ROLE, SUPERVISOR_ROLE)
def dashboard(request):
    applications = _visible_applications(request.user)
    context = {
        'applications': applications,
        'role_label': get_role_label(request.user),
        'is_marketing': has_role(request.user, MARKETING_ROLE),
        'is_supervisor': has_role(request.user, SUPERVISOR_ROLE),
    }
    return render(request, 'credit_digitalization/dashboard.html', context)


@role_required(MARKETING_ROLE)
def application_create(request):
    if request.method == 'POST':
        form = CreditApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.created_by = request.user
            application.save()
            ApplicationAuditTrail.objects.create(
                application=application,
                actor=request.user,
                action=ApplicationAuditTrail.Action.CREATED,
                to_status=CreditApplication.Status.DRAFT,
                notes='Draft pengajuan dibuat.',
            )
            messages.success(request, 'Draft pengajuan berhasil dibuat.')
            return redirect('credit_digitalization:application_detail', pk=application.pk)
    else:
        form = CreditApplicationForm()
    return render(request, 'credit_digitalization/application_form.html', {
        'form': form,
        'page_title': 'Pengajuan Baru',
        'submit_label': 'Simpan Draft',
    })


@role_required(MARKETING_ROLE, SUPERVISOR_ROLE)
def application_detail(request, pk):
    application = _get_visible_application(request.user, pk)
    context = {
        'application': application,
        'review_form': ReviewForm(),
        'is_marketing': has_role(request.user, MARKETING_ROLE),
        'is_supervisor': has_role(request.user, SUPERVISOR_ROLE),
        'can_review': (
            has_role(request.user, SUPERVISOR_ROLE)
            and application.status == CreditApplication.Status.SUBMITTED
            and application.created_by_id != request.user.id
        ),
    }
    return render(request, 'credit_digitalization/application_detail.html', context)


@role_required(MARKETING_ROLE)
def application_edit(request, pk):
    application = get_object_or_404(
        CreditApplication,
        pk=pk,
        created_by=request.user,
    )
    if application.status != CreditApplication.Status.DRAFT:
        raise PermissionDenied('Hanya pengajuan berstatus Draft yang dapat diubah.')

    if request.method == 'POST':
        form = CreditApplicationForm(
            request.POST, request.FILES, instance=application
        )
        if form.is_valid():
            application = form.save()
            ApplicationAuditTrail.objects.create(
                application=application,
                actor=request.user,
                action=ApplicationAuditTrail.Action.UPDATED,
                from_status=CreditApplication.Status.DRAFT,
                to_status=CreditApplication.Status.DRAFT,
                notes='Data draft diperbarui.',
            )
            messages.success(request, 'Perubahan draft berhasil disimpan.')
            return redirect('credit_digitalization:application_detail', pk=application.pk)
    else:
        form = CreditApplicationForm(instance=application)
    return render(request, 'credit_digitalization/application_form.html', {
        'form': form,
        'application': application,
        'page_title': f'Ubah {application.application_number}',
        'submit_label': 'Simpan Perubahan',
    })


@require_POST
@role_required(MARKETING_ROLE)
def application_submit(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            CreditApplication.objects.select_for_update(),
            pk=pk,
            created_by=request.user,
        )
        if application.status != CreditApplication.Status.DRAFT:
            messages.error(request, 'Hanya pengajuan Draft yang dapat diajukan.')
        elif not application.is_complete:
            messages.error(
                request,
                'Pengajuan belum lengkap. Lengkapi seluruh data dan dokumen.',
            )
        else:
            application.status = CreditApplication.Status.SUBMITTED
            application.submitted_at = timezone.now()
            application.save(update_fields=['status', 'submitted_at', 'updated_at'])
            ApplicationAuditTrail.objects.create(
                application=application,
                actor=request.user,
                action=ApplicationAuditTrail.Action.SUBMITTED,
                from_status=CreditApplication.Status.DRAFT,
                to_status=CreditApplication.Status.SUBMITTED,
                notes='Pengajuan dikirim untuk review Atasan Marketing.',
            )
            messages.success(request, 'Pengajuan berhasil dikirim untuk approval.')
    return redirect('credit_digitalization:application_detail', pk=pk)


@require_POST
@role_required(SUPERVISOR_ROLE)
def application_review(request, pk):
    form = ReviewForm(request.POST)
    with transaction.atomic():
        application = get_object_or_404(
            _visible_applications(request.user).select_for_update(), pk=pk
        )
        if application.created_by_id == request.user.id:
            raise PermissionDenied(
                'Maker tidak dapat melakukan approval terhadap pengajuannya sendiri.'
            )
        if application.status != CreditApplication.Status.SUBMITTED:
            messages.error(request, 'Pengajuan ini sudah diproses atau belum diajukan.')
            return redirect('credit_digitalization:application_detail', pk=pk)
        if not form.is_valid():
            context = {
                'application': application,
                'review_form': form,
                'is_marketing': has_role(request.user, MARKETING_ROLE),
                'is_supervisor': True,
                'can_review': True,
            }
            return render(
                request,
                'credit_digitalization/application_detail.html',
                context,
                status=400,
            )

        decision = form.cleaned_data['decision']
        notes = form.cleaned_data['notes'].strip()
        application.status = decision
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.rejection_reason = (
            notes if decision == CreditApplication.Status.REJECTED else ''
        )
        application.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at',
            'rejection_reason', 'updated_at',
        ])
        action = (
            ApplicationAuditTrail.Action.APPROVED
            if decision == CreditApplication.Status.APPROVED
            else ApplicationAuditTrail.Action.REJECTED
        )
        ApplicationAuditTrail.objects.create(
            application=application,
            actor=request.user,
            action=action,
            from_status=CreditApplication.Status.SUBMITTED,
            to_status=decision,
            notes=notes or 'Pengajuan memenuhi kriteria approval.',
        )
        message = (
            'Pengajuan berhasil disetujui.'
            if decision == CreditApplication.Status.APPROVED
            else 'Pengajuan telah ditolak.'
        )
        messages.success(request, message)
    return redirect('credit_digitalization:application_detail', pk=pk)


@role_required(MARKETING_ROLE, SUPERVISOR_ROLE)
def document_download(request, pk, field_name):
    application = _get_visible_application(request.user, pk)
    allowed_fields = {
        'ktp': 'ktp_document',
        'family-card': 'family_card_document',
        'booking-fee': 'booking_fee_document',
        'application-form': 'application_form_document',
    }
    model_field = allowed_fields.get(field_name)
    if not model_field:
        raise Http404
    document = getattr(application, model_field)
    if not document:
        raise Http404
    try:
        return FileResponse(
            document.open('rb'),
            as_attachment=True,
            filename=Path(document.name).name,
        )
    except FileNotFoundError as exc:
        raise Http404 from exc
