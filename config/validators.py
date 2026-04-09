from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError


class StrengthPasswordValidator:
    """
    Validate that password contains mix of letters, numbers, and special characters.
    """
    def validate(self, password, user=None):
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

        if not (has_upper and has_lower and has_digit):
            raise ValidationError(
                'Password must contain uppercase letters, lowercase letters, and numbers.',
                code='password_too_weak',
            )

    def get_help_text(self):
        return 'Your password must contain uppercase letters, lowercase letters, and numbers.'
