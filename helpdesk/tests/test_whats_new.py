import frappe
from frappe.tests import IntegrationTestCase

from helpdesk import whats_new
from helpdesk.test_utils import (
    create_agent,
    unique_email,
    use_whats_new_notes,
    whats_new_note,
    write_whats_new_notes,
)


def titles(notes: list[dict]) -> list[str]:
    return [note["title"] for note in notes]


class TestWhatsNew(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_notes_sort_unreleased_first_then_newest_version(self) -> None:
        use_whats_new_notes(
            self,
            {
                "a": whats_new_note("Old", "0.9.0", date="2026-01-01"),
                "b": whats_new_note("Newer", "0.10.0", date="2026-02-01"),
                "c": whats_new_note("Soon"),
            },
        )
        self.assertEqual(titles(whats_new.load_notes()), ["Soon", "Newer", "Old"])

    def test_group_by_release_groups_same_version(self) -> None:
        use_whats_new_notes(
            self,
            {
                "a": whats_new_note("A", "1.0.0", date="2026-03-01"),
                "b": whats_new_note("B", "1.0.0", date="2026-03-01"),
                "c": whats_new_note("C", "0.9.0", date="2026-01-01"),
            },
        )
        releases = whats_new.group_by_release(whats_new.load_notes())
        self.assertEqual(
            [(r["version"], r["date"], titles(r["notes"])) for r in releases],
            [("1.0.0", "2026-03-01", ["A", "B"]), ("0.9.0", "2026-01-01", ["C"])],
        )

    def test_unreleased_group_has_no_version_or_date(self) -> None:
        use_whats_new_notes(self, {"a": whats_new_note("A", date="2026-03-01")})
        (release,) = whats_new.group_by_release(whats_new.load_notes())
        self.assertEqual((release["version"], release["date"]), (None, None))

    def test_body_is_rendered_markdown(self) -> None:
        use_whats_new_notes(self, {"a": whats_new_note("A", body="Be **bold**")})
        self.assertIn("<strong>bold</strong>", whats_new.load_notes()[0]["body"])

    def test_media_resolves_light_and_dark(self) -> None:
        media_dir = use_whats_new_notes(
            self,
            {
                "a": whats_new_note("A", media="a.png"),
                "b": whats_new_note("B", media="b.mp4"),
            },
        )
        for name in ("a.png", "a.dark.png", "b.mp4"):
            (media_dir / name).write_bytes(b"x")
        whats_new.load_notes.cache_clear()
        by_title = {note["title"]: note["media"] for note in whats_new.load_notes()}
        self.assertEqual(
            by_title["A"],
            {
                "url": "/assets/helpdesk/whats_new/a.png",
                "dark_url": "/assets/helpdesk/whats_new/a.dark.png",
                "kind": "image",
            },
        )
        self.assertEqual(by_title["B"]["kind"], "video")
        self.assertIsNone(by_title["B"]["dark_url"])

    def test_media_that_is_missing_or_a_path_is_ignored(self) -> None:
        use_whats_new_notes(
            self,
            {
                "a": whats_new_note("Missing", media="nope.png"),
                "b": whats_new_note("Escaping", media="../x.png"),
            },
        )
        self.assertEqual([note["media"] for note in whats_new.load_notes()], [None] * 2)

    def test_malformed_notes_are_skipped(self) -> None:
        use_whats_new_notes(
            self,
            {
                "plain": "Just text, no frontmatter",
                "untitled": "---\nversion: unreleased\n---\nBody\n",
                "good": whats_new_note("Good"),
            },
        )
        self.assertEqual(titles(whats_new.load_notes()), ["Good"])

    def test_unseen_until_marked_per_user(self) -> None:
        use_whats_new_notes(self, {"a": whats_new_note("A"), "b": whats_new_note("B")})
        first = create_agent(unique_email("seen-first")).name
        second = create_agent(unique_email("seen-second")).name
        whats_new.mark_all_seen(first)
        self.assertEqual(whats_new.get_unseen_notes(first), [])
        self.assertEqual(len(whats_new.get_unseen_notes(second)), 2)

    def test_note_added_after_marking_is_unseen_even_if_it_sorts_last(self) -> None:
        use_whats_new_notes(self, {"a": whats_new_note("New", "2.0.0")})
        agent = create_agent(unique_email("seen-later")).name
        whats_new.mark_all_seen(agent)
        write_whats_new_notes(
            whats_new.NOTES_DIR, {"b": whats_new_note("Backfilled", "1.0.0")}
        )
        self.assertEqual(titles(whats_new.get_unseen_notes(agent)), ["Backfilled"])

    def test_seen_state_survives_a_cache_clear(self) -> None:
        use_whats_new_notes(self, {"a": whats_new_note("A")})
        agent = create_agent(unique_email("seen-cache")).name
        whats_new.mark_all_seen(agent)
        frappe.clear_cache(user=agent)
        self.assertEqual(whats_new.get_unseen_notes(agent), [])
