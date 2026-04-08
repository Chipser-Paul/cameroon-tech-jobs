from companies.models import Company
from seekers.models import Seeker


def notification_counts(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'navbar_unread_notifications': 0}

    user = request.user
    if isinstance(user, Company):
        count = user.notifications.filter(is_read=False).count()
    elif isinstance(user, Seeker):
        count = user.notifications.filter(is_read=False).count()
    else:
        count = 0

    return {'navbar_unread_notifications': count}
