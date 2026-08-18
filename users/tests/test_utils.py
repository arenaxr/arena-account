"""Tests for the pure date helpers in users/utils.py.

`parse_persist_date` normalizes whatever the Mongo persist database returns into
an aware datetime, and `apply_updated_at` merges that with each row's own
creation date to produce the "last activity" column and its sort order. Both are
pure functions over dicts, so no database and no Mongo connection is needed.
"""

import datetime

from django.test import SimpleTestCase
from django.utils import timezone

from users.utils import apply_updated_at, parse_persist_date

UTC = datetime.timezone.utc


class ParsePersistDateTests(SimpleTestCase):
    def test_falsy_values_return_none(self):
        for value in [None, "", 0, [], {}]:
            with self.subTest(value=value):
                self.assertIsNone(parse_persist_date(value))

    def test_iso_string_with_zulu_suffix(self):
        self.assertEqual(
            parse_persist_date("2026-01-02T03:04:05Z"),
            datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        )

    def test_iso_string_with_fractional_seconds_and_zulu_suffix(self):
        self.assertEqual(
            parse_persist_date("2026-01-02T03:04:05.123Z"),
            datetime.datetime(2026, 1, 2, 3, 4, 5, 123000, tzinfo=UTC),
        )

    def test_iso_string_with_explicit_offset_is_preserved(self):
        parsed = parse_persist_date("2026-01-02T03:04:05+02:00")
        self.assertEqual(parsed.utcoffset(), datetime.timedelta(hours=2))
        self.assertEqual(parsed, datetime.datetime(2026, 1, 2, 1, 4, 5, tzinfo=UTC))

    def test_naive_iso_string_is_coerced_to_utc(self):
        parsed = parse_persist_date("2026-01-02T03:04:05")
        self.assertFalse(timezone.is_naive(parsed))
        self.assertEqual(parsed, datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC))

    def test_date_only_string(self):
        self.assertEqual(
            parse_persist_date("2026-01-02"),
            datetime.datetime(2026, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

    def test_unparseable_string_returns_none(self):
        for value in ["not a date", "2026-13-45T99:99:99Z", "yesterday"]:
            with self.subTest(value=value):
                self.assertIsNone(parse_persist_date(value))

    def test_unsupported_types_return_none(self):
        for value in [123, 1.5, ["2026-01-02"], {"d": "2026-01-02"}, True]:
            with self.subTest(value=value):
                self.assertIsNone(parse_persist_date(value))

    def test_aware_datetime_passes_through_unchanged(self):
        value = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
        self.assertIs(parse_persist_date(value), value)

    def test_naive_datetime_is_made_aware_in_utc(self):
        parsed = parse_persist_date(datetime.datetime(2026, 1, 2, 3, 4, 5))
        self.assertFalse(timezone.is_naive(parsed))
        self.assertEqual(parsed, datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC))

    def test_date_instance_is_rejected(self):
        """A datetime.date is not a datetime.datetime, so it is not accepted."""
        self.assertIsNone(parse_persist_date(datetime.date(2026, 1, 2)))


def dt(day, hour=0):
    return datetime.datetime(2026, 1, day, hour, 0, 0, tzinfo=UTC)


class ApplyUpdatedAtTests(SimpleTestCase):
    def test_persist_value_newer_than_creation_date_wins(self):
        items = [{"name": "ns/scene", "creation_date": dt(1)}]
        result = apply_updated_at(items, {"ns/scene": "2026-01-05T00:00:00Z"})
        self.assertEqual(result[0]["updated_at"], dt(5))

    def test_creation_date_newer_than_persist_value_wins(self):
        items = [{"name": "ns/scene", "creation_date": dt(9)}]
        result = apply_updated_at(items, {"ns/scene": "2026-01-05T00:00:00Z"})
        self.assertEqual(result[0]["updated_at"], dt(9))

    def test_dict_persist_value_sets_persist_count(self):
        items = [{"name": "ns/scene", "creation_date": dt(1)}]
        result = apply_updated_at(
            items, {"ns/scene": {"last_updated": "2026-01-05T00:00:00Z", "count": 7}}
        )
        self.assertEqual(result[0]["updated_at"], dt(5))
        self.assertEqual(result[0]["persist_count"], 7)

    def test_dict_persist_value_without_count_defaults_to_zero(self):
        items = [{"name": "ns/scene", "creation_date": dt(1)}]
        result = apply_updated_at(items, {"ns/scene": {"last_updated": "2026-01-05T00:00:00Z"}})
        self.assertEqual(result[0]["persist_count"], 0)

    def test_dict_persist_value_with_unparseable_date_falls_back_to_creation_date(self):
        items = [{"name": "ns/scene", "creation_date": dt(1)}]
        result = apply_updated_at(items, {"ns/scene": {"last_updated": "bogus", "count": 3}})
        self.assertEqual(result[0]["updated_at"], dt(1))
        self.assertEqual(result[0]["persist_count"], 3)

    def test_scalar_persist_value_does_not_set_persist_count(self):
        items = [{"name": "ns/scene", "creation_date": dt(1)}]
        result = apply_updated_at(items, {"ns/scene": "2026-01-05T00:00:00Z"})
        self.assertNotIn("persist_count", result[0])

    def test_missing_persist_entry_uses_creation_date(self):
        items = [{"name": "ns/scene", "creation_date": dt(3)}]
        result = apply_updated_at(items, {})
        self.assertEqual(result[0]["updated_at"], dt(3))

    def test_persist_only_entry_uses_persist_date(self):
        items = [{"name": "ns/scene"}]
        result = apply_updated_at(items, {"ns/scene": "2026-01-05T00:00:00Z"})
        self.assertEqual(result[0]["updated_at"], dt(5))

    def test_no_dates_at_all_gives_none(self):
        items = [{"name": "ns/scene"}]
        result = apply_updated_at(items, {})
        self.assertIsNone(result[0]["updated_at"])

    def test_sorted_newest_first_with_undated_items_last(self):
        items = [
            {"name": "old", "creation_date": dt(1)},
            {"name": "undated"},
            {"name": "newest", "creation_date": dt(20)},
            {"name": "middle", "creation_date": dt(10)},
        ]
        result = apply_updated_at(items, {})
        self.assertEqual([i["name"] for i in result], ["newest", "middle", "old", "undated"])

    def test_persist_activity_reorders_rows(self):
        items = [
            {"name": "a", "creation_date": dt(1)},
            {"name": "b", "creation_date": dt(2)},
        ]
        result = apply_updated_at(items, {"a": "2026-01-30T00:00:00Z"})
        self.assertEqual([i["name"] for i in result], ["a", "b"])

    def test_empty_input(self):
        self.assertEqual(apply_updated_at([], {}), [])

    def test_annotates_items_in_place_and_returns_same_objects(self):
        item = {"name": "ns/scene", "creation_date": dt(1)}
        result = apply_updated_at([item], {})
        self.assertIs(result[0], item)
        self.assertIn("updated_at", item)
