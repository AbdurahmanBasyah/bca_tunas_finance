from .access import get_role_label


def user_role(request):
    if request.user.is_authenticated:
        return {'current_role_label': get_role_label(request.user)}
    return {'current_role_label': ''}
