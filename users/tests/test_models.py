"""Tests for the pure parts of users/models.py.

Only the string properties and the namespace/id validators are covered here;
they run on unsaved instances, so no database is touched. `is_default` is
deliberately left out because it counts related editor/viewer rows.
"""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from users.models import (
    RE_PATTERN_NS_SLASH_ID,
    Device,
    Namespace,
    NamespaceDefault,
    Scene,
    SceneDefault,
    ns_regex,
    ns_slash_id_regex,
)


class SceneStringPropertyTests(SimpleTestCase):
    def test_namespace_and_sceneid_split_on_slash(self):
        scene = Scene(name="bob/scene1")
        self.assertEqual(scene.namespace, "bob")
        self.assertEqual(scene.sceneid, "scene1")

    def test_str_is_the_full_name(self):
        self.assertEqual(str(Scene(name="bob/scene1")), "bob/scene1")

    def test_namespace_without_slash_returns_whole_name(self):
        self.assertEqual(Scene(name="bob").namespace, "bob")

    def test_sceneid_without_slash_raises_indexerror(self):
        """Callers must only read sceneid on a validated namespace/scene name."""
        with self.assertRaises(IndexError):
            Scene(name="bob").sceneid

    def test_clean_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            Scene(name="").clean()

    def test_clean_strips_surrounding_whitespace(self):
        scene = Scene(name="  bob/scene1  ")
        scene.clean()
        self.assertEqual(scene.name, "bob/scene1")


class DeviceStringPropertyTests(SimpleTestCase):
    def test_namespace_and_deviceid_split_on_slash(self):
        device = Device(name="bob/dev1")
        self.assertEqual(device.namespace, "bob")
        self.assertEqual(device.deviceid, "dev1")

    def test_str_is_the_full_name(self):
        self.assertEqual(str(Device(name="bob/dev1")), "bob/dev1")

    def test_clean_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            Device(name="").clean()


class NamespaceTests(SimpleTestCase):
    def test_str_is_the_name(self):
        self.assertEqual(str(Namespace(name="bob")), "bob")

    def test_clean_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            Namespace(name="").clean()

    def test_clean_strips_surrounding_whitespace(self):
        namespace = Namespace(name=" bob ")
        namespace.clean()
        self.assertEqual(namespace.name, "bob")


class NamespaceRegexTests(SimpleTestCase):
    VALID = ["bob", "bob_1", "bob-1", "bob.1", "BOB", "b0b", ""]
    INVALID = ["bob/scene", "bob scene", "bob!", "bob@example.com", "bob#1", "bob+1"]

    def test_accepts_namespace_names(self):
        for name in self.VALID:
            with self.subTest(name=name):
                ns_regex(name)

    def test_rejects_namespace_names(self):
        for name in self.INVALID:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    ns_regex(name)


class NamespaceSlashIdRegexTests(SimpleTestCase):
    VALID = ["bob/scene1", "bob-1/scene.2", "b_o_b/S-C.E_1", "public/lobby"]
    INVALID = [
        "",
        "bob",
        "bob/",
        "/scene1",
        "bob/scene/extra",
        "bob//scene1",
        "bob scene/scene1",
        "bob/scene 1",
        "bob/scene!",
        "bob\\scene1",
    ]

    def test_accepts_namespaced_ids(self):
        for name in self.VALID:
            with self.subTest(name=name):
                ns_slash_id_regex(name)
                self.assertIsNotNone(RE_PATTERN_NS_SLASH_ID.match(name))

    def test_rejects_bad_namespaced_ids(self):
        for name in self.INVALID:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    ns_slash_id_regex(name)
                self.assertIsNone(RE_PATTERN_NS_SLASH_ID.match(name))


class DefaultPlaceholderTests(SimpleTestCase):
    """The *Default classes stand in for rows that only exist in the persist db."""

    def test_namespace_default_shape(self):
        placeholder = vars(NamespaceDefault(name="bob"))
        self.assertEqual(
            placeholder,
            {"name": "bob", "editors": [], "viewers": [], "is_default": True},
        )

    def test_scene_default_shape(self):
        placeholder = vars(SceneDefault(name="bob/scene1"))
        self.assertEqual(
            placeholder,
            {
                "name": "bob/scene1",
                "editors": [],
                "viewers": [],
                "public_read": True,
                "public_write": False,
                "anonymous_users": True,
                "video_conference": True,
                "users": True,
                "is_default": True,
            },
        )

    def test_scene_default_matches_model_field_defaults(self):
        placeholder = SceneDefault(name="bob/scene1")
        model_defaults = Scene(name="bob/scene1")
        for flag in ("public_read", "public_write", "anonymous_users", "video_conference", "users"):
            with self.subTest(flag=flag):
                self.assertEqual(getattr(placeholder, flag), getattr(model_defaults, flag))
