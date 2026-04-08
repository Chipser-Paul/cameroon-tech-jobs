from .models import Notification


def notify_company(company, title, body, link=''):
    return Notification.objects.create(
        recipient_company=company,
        title=title,
        body=body,
        link=link,
    )


def notify_seeker(seeker, title, body, link=''):
    return Notification.objects.create(
        recipient_seeker=seeker,
        title=title,
        body=body,
        link=link,
    )
