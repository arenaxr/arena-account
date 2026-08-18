"""Tests for the pure topic helpers in users/mqtt.py.

`clean_topics` shrinks the permission arrays that go into every MQTT token, and
the topicv2_add_* builders define the exact topic grammar every ARENA client
depends on. Both are pure list-in/list-out, so no database is needed.
"""

import unittest

from users.mqtt import (
    clean_topics,
    topicv2_add_evhost,
    topicv2_add_rrhost,
    topicv2_add_scene_reader,
    topicv2_add_scene_writer,
)


class CleanTopicsTests(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(clean_topics([]), [])

    def test_removes_duplicates(self):
        self.assertEqual(clean_topics(["realm/s/ns/scene", "realm/s/ns/scene"]), ["realm/s/ns/scene"])

    def test_sorts_output(self):
        self.assertEqual(
            clean_topics(["realm/s/b/x", "realm/s/a/x", "$NETWORK/latency"]),
            ["$NETWORK/latency", "realm/s/a/x", "realm/s/b/x"],
        )

    def test_collapses_topic_covered_by_multilevel_wildcard(self):
        self.assertEqual(
            clean_topics(["realm/s/#", "realm/s/ns/scene", "realm/s/ns/scene/o/uc/obj"]),
            ["realm/s/#"],
        )

    def test_collapses_topic_covered_by_singlelevel_wildcard(self):
        self.assertEqual(
            clean_topics(["realm/s/+/scene", "realm/s/ns/scene"]),
            ["realm/s/+/scene"],
        )

    def test_keeps_unrelated_topics(self):
        topics = [
            "realm/d/bob/#",
            "realm/s/bob/+/o/bob_1_web/#",
            "realm/s/carol/shared/+/+/+",
            "$NETWORK/latency",
        ]
        self.assertEqual(clean_topics(topics), sorted(topics))

    def test_sibling_wildcards_do_not_collapse_each_other(self):
        self.assertEqual(
            clean_topics(["realm/s/bob/#", "realm/s/carol/#"]),
            ["realm/s/bob/#", "realm/s/carol/#"],
        )

    def test_collapses_render_fusion_pub_into_presence_pub(self):
        """The real overlap that shrinks scene tokens: '+/uc/uid/+' covers 'r/uc/uid/-'."""
        topics = [
            "realm/s/ns/scene/+/uc/uid",
            "realm/s/ns/scene/+/uc/uid/+",
            "realm/s/ns/scene/r/uc/uid/-",
            "realm/s/ns/scene/e/uc/uid/-",
            "realm/s/ns/scene/d/uc/uid/-",
        ]
        self.assertEqual(
            clean_topics(topics),
            ["realm/s/ns/scene/+/uc/uid", "realm/s/ns/scene/+/uc/uid/+"],
        )

    def test_dollar_topic_is_not_collapsed_by_leading_wildcard(self):
        """'#' does not cover '$'-prefixed topics, so both survive."""
        self.assertEqual(clean_topics(["#", "$NETWORK/latency"]), ["#", "$NETWORK/latency"])

    def test_parent_level_of_hash_filter_is_not_collapsed(self):
        """Known shape: 'realm/s' sorts before 'realm/s/#' so the pair is kept.

        '#' does match its own parent level, but the collapse only looks
        backwards through the sorted list, so this redundancy survives. Harmless
        (the token is just slightly larger), pinned here so a change is visible.
        """
        self.assertEqual(clean_topics(["realm/s/#", "realm/s"]), ["realm/s", "realm/s/#"])

    def test_is_idempotent(self):
        topics = [
            "realm/s/#",
            "realm/s/ns/scene",
            "realm/d/bob/#",
            "realm/d/bob/#",
            "$NETWORK/latency",
        ]
        once = clean_topics(topics)
        self.assertEqual(clean_topics(once), once)

    def test_does_not_mutate_input(self):
        topics = ["realm/s/b", "realm/s/a", "realm/s/a"]
        clean_topics(topics)
        self.assertEqual(topics, ["realm/s/b", "realm/s/a", "realm/s/a"])


class Topicv2BuilderTests(unittest.TestCase):
    """Pin the exact v2 topic grammar; clients parse these level by level."""

    def setUp(self):
        self.pubs = []
        self.subs = []
        self.ids = {"userid": "bob_1", "userclient": "bob_1_web"}

    def test_scene_reader_without_userid(self):
        topicv2_add_scene_reader(self.pubs, self.subs, "realm", "ns", "scene", {})
        self.assertEqual(self.pubs, [])
        self.assertEqual(self.subs, ["realm/s/ns/scene/+/+/+"])

    def test_scene_reader_with_userid(self):
        topicv2_add_scene_reader(self.pubs, self.subs, "realm", "ns", "scene", self.ids)
        self.assertEqual(self.pubs, [])
        self.assertEqual(
            self.subs,
            [
                "realm/s/ns/scene/+/+/+",
                "realm/s/ns/scene/+/+/+/bob_1/#",
            ],
        )

    def test_scene_reader_accepts_wildcard_namespace_and_scene(self):
        topicv2_add_scene_reader(self.pubs, self.subs, "realm", "+", "+", self.ids)
        self.assertEqual(
            self.subs,
            [
                "realm/s/+/+/+/+/+",
                "realm/s/+/+/+/+/+/bob_1/#",
            ],
        )

    def test_scene_writer_without_userid(self):
        # no 'userid' key: the writer still gets object and program topics
        topicv2_add_scene_writer(self.pubs, self.subs, "realm", "ns", "scene", {"userclient": "bob_1_web"})
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/o/bob_1_web/#",
                "realm/s/ns/scene/p/bob_1_web/+",
                "realm/s/ns/scene/p/+/#",
            ],
        )
        self.assertEqual(self.subs, ["realm/s/ns/scene/p/+/#"])

    def test_scene_writer_with_userid(self):
        topicv2_add_scene_writer(self.pubs, self.subs, "realm", "ns", "scene", self.ids)
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/o/bob_1_web/#",
                "realm/s/ns/scene/p/bob_1_web/+",
                "realm/s/ns/scene/o/bob_1_web/+/+",
                "realm/s/ns/scene/p/+/#",
            ],
        )
        self.assertEqual(self.subs, ["realm/s/ns/scene/p/+/#"])

    def test_scene_writer_adds_render_fusion_host_topics(self):
        ids = dict(self.ids, renderfusionid="-")
        topicv2_add_scene_writer(self.pubs, self.subs, "realm", "ns", "scene", ids)
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/o/bob_1_web/#",
                "realm/s/ns/scene/p/bob_1_web/+",
                "realm/s/ns/scene/o/bob_1_web/+/+",
                "realm/s/ns/scene/r/bob_1_web/-",
                "realm/s/ns/scene/r/bob_1_web/-/+",
                "realm/s/ns/scene/p/+/#",
            ],
        )
        self.assertEqual(
            self.subs,
            [
                "realm/s/ns/scene/r/+/+/-/#",
                "realm/s/ns/scene/p/+/#",
            ],
        )

    def test_scene_writer_adds_environment_host_topics(self):
        ids = dict(self.ids, environmentid="-")
        topicv2_add_scene_writer(self.pubs, self.subs, "realm", "ns", "scene", ids)
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/o/bob_1_web/#",
                "realm/s/ns/scene/p/bob_1_web/+",
                "realm/s/ns/scene/o/bob_1_web/+/+",
                "realm/s/ns/scene/e/bob_1_web/-",
                "realm/s/ns/scene/e/bob_1_web/-/+",
                "realm/s/ns/scene/p/+/#",
            ],
        )
        self.assertEqual(
            self.subs,
            [
                "realm/s/ns/scene/e/+/+/-/#",
                "realm/s/ns/scene/p/+/#",
            ],
        )

    def test_rrhost_topics(self):
        topicv2_add_rrhost(self.pubs, self.subs, "realm", "ns", "scene", "bob_1_web")
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/r/bob_1_web/-",
                "realm/s/ns/scene/r/bob_1_web/-/+",
            ],
        )
        self.assertEqual(self.subs, ["realm/s/ns/scene/r/+/+/-/#"])

    def test_evhost_topics(self):
        topicv2_add_evhost(self.pubs, self.subs, "realm", "ns", "scene", "bob_1_web")
        self.assertEqual(
            self.pubs,
            [
                "realm/s/ns/scene/e/bob_1_web/-",
                "realm/s/ns/scene/e/bob_1_web/-/+",
            ],
        )
        self.assertEqual(self.subs, ["realm/s/ns/scene/e/+/+/-/#"])

    def test_builders_append_to_existing_lists(self):
        self.pubs.append("$NETWORK/latency")
        self.subs.append("$NETWORK")
        topicv2_add_scene_reader(self.pubs, self.subs, "realm", "ns", "scene", {})
        self.assertEqual(self.pubs, ["$NETWORK/latency"])
        self.assertEqual(self.subs, ["$NETWORK", "realm/s/ns/scene/+/+/+"])
