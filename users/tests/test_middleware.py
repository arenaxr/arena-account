"""Tests for users/middleware.py VersioningMiddleware.

process_view maps the resolved URL namespace onto request.version, which every
API view reads to decide which topic layout to issue. Pure string dispatch: no
database, no real request cycle.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from users.middleware import VersioningMiddleware
from users.versioning import API_V1, API_V2, SUPPORTED_API_VERSIONS


def fake_request(namespace=None, has_match=True):
    resolver_match = SimpleNamespace(namespace=namespace) if has_match else None
    return SimpleNamespace(resolver_match=resolver_match)


class VersioningMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.sentinel = object()
        self.middleware = VersioningMiddleware(lambda request: self.sentinel)

    def process(self, request):
        result = self.middleware.process_view(request, None, [], {})
        # process_view must never short-circuit the request
        self.assertIsNone(result)
        return request.version

    def test_call_delegates_to_next_handler(self):
        self.assertIs(self.middleware(fake_request()), self.sentinel)

    def test_bare_version_namespace(self):
        self.assertEqual(self.process(fake_request("v1")), API_V1)
        self.assertEqual(self.process(fake_request("v2")), API_V2)

    def test_api_prefixed_namespace(self):
        self.assertEqual(self.process(fake_request("api_v1")), API_V1)
        self.assertEqual(self.process(fake_request("api_v2")), API_V2)

    def test_unknown_namespace_falls_back_to_first_supported_version(self):
        for namespace in ["users", "admin", "api_v9", "api_", "V2", "v2x"]:
            with self.subTest(namespace=namespace):
                self.assertEqual(self.process(fake_request(namespace)), SUPPORTED_API_VERSIONS[0])

    def test_empty_namespace_falls_back(self):
        self.assertEqual(self.process(fake_request("")), SUPPORTED_API_VERSIONS[0])

    def test_missing_resolver_match_falls_back(self):
        self.assertEqual(
            self.process(fake_request(has_match=False)), SUPPORTED_API_VERSIONS[0]
        )

    def test_first_supported_version_is_v1(self):
        """The fallback above is only sane while v1 stays first in the list."""
        self.assertEqual(SUPPORTED_API_VERSIONS[0], API_V1)
