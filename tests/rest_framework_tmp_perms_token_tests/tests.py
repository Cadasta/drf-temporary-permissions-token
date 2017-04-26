import unittest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework_tmp_perms_token.auth import ApiTokenAuthentication
from rest_framework_tmp_perms_token.token import TemporaryApiToken


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user, _ = get_user_model()._default_manager.get_or_create()

    def test_valid_request(self):
        t = TemporaryApiToken(
            user=self.user,
            endpoints=dict(GET=['/bar'], POST=['/foo']),
            max_age=10,
            recipient='my-new-microservice'
        )
        request = self.factory.post(
            '/foo/some-nested-endpoint/',
            Authorization="Token " + t.generate_signed_token()
        )
        ApiTokenAuthentication().authenticate(request)
        recipient = request.META.get('X-API-Token-Recipient')
        assert recipient == "my-new-microservice"

    def test_valid_request_query_arg(self):
        """ Ensure that auth token can be encloded as GET parameter """
        t = TemporaryApiToken(
            user=self.user,
            endpoints=dict(GET=['/foo', '/bar'], POST=['/foo']),
            max_age=10,
            recipient='my-new-microservice'
        )
        request = self.factory.get(
            '/foo/some-nested-endpoint/',
            data={'AUTH_TOKEN': t.generate_signed_token()}
        )
        ApiTokenAuthentication().authenticate(request)
        recipient = request.META.get('X-API-Token-Recipient')
        assert recipient == "my-new-microservice"

    def test_invalid_path_request(self):
        """ Ensure that not-permitted paths throws exception """
        t = TemporaryApiToken(
            user=self.user,
            endpoints=dict(GET=['/foo', '/bar'], POST=['/foo']),
            max_age=10,
            recipient='my-new-microservice'
        )
        request = self.factory.get(
            '/secret',
            Authorization="Token " + t.generate_signed_token()
        )
        try:
            ApiTokenAuthentication().authenticate(request)
        except Exception as e:
            assert str(e) == "Endpoint interaction not permitted by token", \
                "Wrong err: {}".format(e)
        else:
            assert 0, "Token did not throw error!"

    def test_expired_token_request(self):
        """ Ensure that expired tokens throws exception """
        t = TemporaryApiToken(
            user=self.user,
            endpoints=dict(GET=['/foo']),
            max_age=0  # Immediately expired
        )
        request = self.factory.get(
            '/foo/bar',
            Authorization="Token " + t.generate_signed_token()
        )
        try:
            ApiTokenAuthentication().authenticate(request)
        except Exception as e:
            assert str(e) == "Token has expired", "Wrong err: {}".format(e)
        else:
            assert 0, "Token did not throw error!"


if __name__ == '__main__':
    unittest.main()