from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    allowed_special_chars = '#@_'  # Define allowed special characters here

    def validate(self, password, user=None):
        pattern = r'^[a-zA-Z0-9{}]+$'.format(re.escape(self.allowed_special_chars))

        # Check if the password contains any invalid characters
        if not re.match(pattern, password):
            raise ValidationError(
                f"Password can only contain alphanumeric characters and the following special characters: {self.allowed_special_chars}",
                code='password_invalid_character',
            )

        # Check for at least one special character
        if not re.search(r'[{}]'.format(re.escape(self.allowed_special_chars)), password):
            raise ValidationError(
                f"Password must contain at least one of the following special characters: {self.allowed_special_chars}",
                code='password_no_special',
            )

    def get_help_text(self):
        return f'Your password must contain only alphanumeric characters and at least one of the following special characters: {self.allowed_special_chars}'
