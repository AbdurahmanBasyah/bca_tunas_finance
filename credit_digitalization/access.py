from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


MARKETING_ROLE = 'Marketing'
SUPERVISOR_ROLE = 'Atasan Marketing'


def has_role(user, role):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=role).exists()
    )


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not any(has_role(request.user, role) for role in roles):
                raise PermissionDenied('Anda tidak memiliki akses untuk aksi ini.')
            return view_func(request, *args, **kwargs)

        return wrapped
    return decorator


def get_role_label(user):
    if user.is_superuser:
        return 'Administrator'
    if has_role(user, SUPERVISOR_ROLE):
        return SUPERVISOR_ROLE
    if has_role(user, MARKETING_ROLE):
        return MARKETING_ROLE
    return 'Tanpa role'
