# coding: utf-8
from onadata.apps.main.tests.test_base import TestBase
from onadata.libs.serializers.password_reset_serializer import \
    get_password_reset_email


class TestPasswordResetEmail(TestBase):

    def test_get_password_reset_email(self):
        """Test base64 username is included in reset email."""
        subject, email = get_password_reset_email(self.user, 'https://ona.io')

        self.assertIn(self.user.username, email,
                      "Username is included in reset email.")
