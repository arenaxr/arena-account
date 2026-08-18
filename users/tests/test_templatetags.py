"""Tests for users/templatetags/users_tags.py short_timesince.

The filter renders the "last activity" column, bucketing an age into a compact
y/mo/w/d/h/m/s string. The bucket boundaries are integer divisions, so each one
is checked on both sides. `timezone.now` is patched so the tests are not racing
the clock.
"""

import datetime
from unittest import mock

from django.test import SimpleTestCase

from users.templatetags.users_tags import short_timesince

NOW = datetime.datetime(2026, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


class ShortTimesinceTests(SimpleTestCase):
    def render(self, **age):
        with mock.patch(
            "users.templatetags.users_tags.timezone.now", return_value=NOW
        ):
            return short_timesince(NOW - datetime.timedelta(**age))

    def test_empty_values_render_empty_string(self):
        for value in [None, "", 0, False]:
            with self.subTest(value=value):
                self.assertEqual(short_timesince(value), "")

    def test_non_datetime_value_renders_empty_string(self):
        """A string that is not a datetime cannot be subtracted; caught as TypeError."""
        self.assertEqual(short_timesince("2026-01-02T03:04:05Z"), "")

    def test_years(self):
        self.assertEqual(self.render(days=365), "1y")
        self.assertEqual(self.render(days=729), "1y")
        self.assertEqual(self.render(days=730), "2y")

    def test_below_a_year_is_months_not_years(self):
        """364 days renders as '12mo': months are checked before weeks."""
        self.assertEqual(self.render(days=364), "12mo")

    def test_months(self):
        self.assertEqual(self.render(days=30), "1mo")
        self.assertEqual(self.render(days=59), "1mo")
        self.assertEqual(self.render(days=60), "2mo")
        self.assertEqual(self.render(days=364), "12mo")  # months run right up to the year bucket

    def test_below_a_month_is_weeks(self):
        self.assertEqual(self.render(days=29), "4w")

    def test_weeks(self):
        self.assertEqual(self.render(days=7), "1w")
        self.assertEqual(self.render(days=13), "1w")
        self.assertEqual(self.render(days=14), "2w")

    def test_below_a_week_is_days(self):
        self.assertEqual(self.render(days=6), "6d")

    def test_days(self):
        self.assertEqual(self.render(days=1), "1d")
        self.assertEqual(self.render(days=1, hours=23), "1d")
        self.assertEqual(self.render(hours=24), "1d")

    def test_below_a_day_is_hours(self):
        self.assertEqual(self.render(hours=23, minutes=59, seconds=59), "23h")

    def test_hours(self):
        self.assertEqual(self.render(seconds=3600), "1h")
        self.assertEqual(self.render(seconds=7199), "1h")
        self.assertEqual(self.render(seconds=7200), "2h")

    def test_below_an_hour_is_minutes(self):
        self.assertEqual(self.render(seconds=3599), "59m")

    def test_minutes(self):
        self.assertEqual(self.render(seconds=60), "1m")
        self.assertEqual(self.render(seconds=119), "1m")
        self.assertEqual(self.render(seconds=120), "2m")

    def test_below_a_minute_is_seconds(self):
        self.assertEqual(self.render(seconds=59), "59s")
        self.assertEqual(self.render(seconds=1), "1s")
        self.assertEqual(self.render(seconds=0), "0s")

    def test_microseconds_are_ignored(self):
        self.assertEqual(self.render(microseconds=500000), "0s")
