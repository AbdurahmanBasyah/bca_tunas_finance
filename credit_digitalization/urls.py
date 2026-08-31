from django.urls import path

from . import views

app_name = 'credit_digitalization'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('applications/new/', views.application_create, name='application_create'),
    path(
        'applications/<int:pk>/',
        views.application_detail,
        name='application_detail',
    ),
    path(
        'applications/<int:pk>/edit/',
        views.application_edit,
        name='application_edit',
    ),
    path(
        'applications/<int:pk>/submit/',
        views.application_submit,
        name='application_submit',
    ),
    path(
        'applications/<int:pk>/review/',
        views.application_review,
        name='application_review',
    ),
    path(
        'applications/<int:pk>/documents/<slug:field_name>/',
        views.document_download,
        name='document_download',
    ),
]
