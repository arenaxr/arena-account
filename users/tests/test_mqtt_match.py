"""Tests for users/mqtt_match.py: MQTT topic filter matching.

`topic_matches_sub` decides whether an issued token permission (a subscription
filter, possibly containing wildcards) covers a concrete topic. `clean_topics`
in users/mqtt.py uses it to collapse token permissions, so its exact wildcard
semantics are load-bearing for what a client is allowed to publish/subscribe.

No database, no settings: plain unittest.TestCase.
"""

import unittest

from users.mqtt_match import MQTTMatcher, topic_matches_sub

# (subscription filter, concrete topic, should match)
MATCH_CASES = [
    # -- exact matches --
    ("sport/tennis/player1", "sport/tennis/player1", True),
    ("sport/tennis/player1", "sport/tennis/player2", False),
    ("sport/tennis", "sport/tennis/player1", False),
    ("sport/tennis/player1", "sport/tennis", False),
    # topic filters are case sensitive
    ("Sport/tennis", "sport/tennis", False),
    ("sport/Tennis", "sport/tennis", False),
    # -- multi-level wildcard '#' --
    ("sport/tennis/#", "sport/tennis/player1", True),
    ("sport/tennis/#", "sport/tennis/player1/score", True),
    # '#' also matches the parent level itself
    ("sport/tennis/#", "sport/tennis", True),
    ("sport/#", "sport", True),
    ("#", "sport/tennis/player1", True),
    ("#", "sport", True),
    # '#' does not match a shorter, unrelated hierarchy
    ("sport/tennis/#", "sport", False),
    ("sport/tennis/#", "sport/football/player1", False),
    # '+' followed by '#' still matches the parent level
    ("sport/+/#", "sport/tennis", True),
    # -- single-level wildcard '+' --
    ("sport/+", "sport/tennis", True),
    ("sport/+", "sport/", True),
    # '+' does not cross a separator
    ("sport/+", "sport/tennis/player1", False),
    # '+' requires a level to be present
    ("sport/+", "sport", False),
    ("non/+/+", "non/matching", False),
    ("sport/+/player1", "sport/tennis/player1", True),
    ("+/tennis/#", "sport/tennis/player1", True),
    # empty levels are levels
    ("+/+", "/finance", True),
    ("/+", "/finance", True),
    ("+", "/finance", False),
    # -- '$'-prefixed topics are not matched by a leading wildcard --
    ("#", "$SYS/broker/uptime", False),
    ("+/monitor/Clients", "$SYS/monitor/Clients", False),
    ("$SYS/#", "$SYS/broker/uptime", True),
    ("$SYS/#", "$SYS", True),
    ("$SYS/monitor/+", "$SYS/monitor/Clients", True),
    # a wildcard below the first level is fine on a '$' topic
    ("$SYS/+/uptime", "$SYS/broker/uptime", True),
    # the ARENA network metrics topics rely on the same rule
    ("$NETWORK/#", "$NETWORK/latency", True),
    ("#", "$NETWORK/latency", False),
    ("$NETWORK", "$NETWORK/latency", False),
    # -- ARENA v2 topic shapes --
    ("realm/s/ns/scene/+/+/+", "realm/s/ns/scene/o/user_1_web/user_1", True),
    ("realm/s/ns/scene/+/+/+", "realm/s/ns/scene/o/user_1_web/user_1/extra", False),
    ("realm/s/+/+/o/user_1_web/#", "realm/s/ns/scene/o/user_1_web/obj/child", True),
    ("realm/s/+/+/o/user_1_web/#", "realm/s/ns/scene/o/other_web/obj", False),
    # this is the overlap that lets clean_topics() drop the render-fusion pub
    ("realm/s/ns/scene/+/user_1_web/user_1/+", "realm/s/ns/scene/r/user_1_web/user_1/-", True),
    ("realm/d/#", "realm/d/bob/dev1/status", True),
    ("realm/d/bob/#", "realm/d/alice/dev1", False),
]


class TopicMatchesSubTests(unittest.TestCase):
    def test_match_table(self):
        for sub, topic, expected in MATCH_CASES:
            with self.subTest(sub=sub, topic=topic):
                self.assertIs(topic_matches_sub(sub, topic), expected)

    def test_wildcard_direction_is_not_symmetric(self):
        """A concrete topic used as a filter does not match a wildcard 'topic'."""
        self.assertTrue(topic_matches_sub("realm/s/#", "realm/s/ns/scene"))
        self.assertFalse(topic_matches_sub("realm/s/ns/scene", "realm/s/#"))


class MQTTMatcherTests(unittest.TestCase):
    def test_set_and_get_item(self):
        matcher = MQTTMatcher()
        matcher["sport/tennis/+"] = "value"
        self.assertEqual(matcher["sport/tennis/+"], "value")

    def test_get_item_unknown_filter_raises_keyerror(self):
        matcher = MQTTMatcher()
        matcher["sport/tennis/+"] = "value"
        with self.assertRaises(KeyError):
            matcher["sport/football/+"]

    def test_get_item_intermediate_node_raises_keyerror(self):
        """A prefix of a stored filter holds no value of its own."""
        matcher = MQTTMatcher()
        matcher["sport/tennis/player1"] = "value"
        with self.assertRaises(KeyError):
            matcher["sport/tennis"]

    def test_del_item_removes_value(self):
        matcher = MQTTMatcher()
        matcher["sport/tennis/+"] = "value"
        del matcher["sport/tennis/+"]
        with self.assertRaises(KeyError):
            matcher["sport/tennis/+"]

    def test_del_item_unknown_filter_raises_keyerror(self):
        matcher = MQTTMatcher()
        with self.assertRaises(KeyError):
            del matcher["sport/tennis/+"]

    def test_del_item_keeps_siblings(self):
        matcher = MQTTMatcher()
        matcher["sport/tennis/player1"] = 1
        matcher["sport/tennis/player2"] = 2
        del matcher["sport/tennis/player1"]
        self.assertEqual(matcher["sport/tennis/player2"], 2)
        self.assertEqual(list(matcher.iter_match("sport/tennis/player2")), [2])
        self.assertEqual(list(matcher.iter_match("sport/tennis/player1")), [])

    def test_iter_match_yields_every_matching_filter(self):
        matcher = MQTTMatcher()
        for i, sub in enumerate(["sport/tennis", "sport/+", "sport/#", "#", "sport/football"]):
            matcher[sub] = i
        self.assertEqual(set(matcher.iter_match("sport/tennis")), {0, 1, 2, 3})

    def test_iter_match_skips_leading_wildcards_for_dollar_topics(self):
        matcher = MQTTMatcher()
        matcher["#"] = "hash"
        matcher["+/latency"] = "plus"
        matcher["$NETWORK/latency"] = "exact"
        matcher["$NETWORK/#"] = "dollar-hash"
        self.assertEqual(
            set(matcher.iter_match("$NETWORK/latency")), {"exact", "dollar-hash"}
        )

    def test_iter_match_no_matches_is_empty(self):
        matcher = MQTTMatcher()
        matcher["realm/d/bob/#"] = True
        self.assertEqual(list(matcher.iter_match("realm/d/alice/dev1")), [])
