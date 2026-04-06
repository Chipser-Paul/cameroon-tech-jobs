from .models import Company


class CompanyBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Company.objects.get(email=username)
            if user.check_password(password):
                return user
        except Company.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Company.objects.get(pk=user_id)
        except Company.DoesNotExist:
            return None