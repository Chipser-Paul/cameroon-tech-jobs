from .models import Seeker


class SeekerBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Seeker.objects.get(email=username)
            if user.check_password(password):
                return user
        except Seeker.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Seeker.objects.get(pk=user_id)
        except Seeker.DoesNotExist:
            return None