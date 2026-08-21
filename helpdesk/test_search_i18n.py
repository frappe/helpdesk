import sqlite3
import unittest

from helpdesk.search_i18n import (
    cjk_index_terms,
    indexed_field_names,
    cjk_ngrams,
    contains_cjk,
    expand_cjk_query,
    normalize_search_text,
)


class TestJapaneseSearch(unittest.TestCase):
    def test_normalization_preserves_japanese_and_normalizes_width(self):
        self.assertEqual(
            normalize_search_text("  ﾊﾟｽﾜｰﾄﾞ変更！ VPN-Error  "),
            "パスワード変更 vpn error",
        )

    def test_cjk_detection(self):
        self.assertTrue(contains_cjk("障害 notification"))
        self.assertTrue(contains_cjk("時々確認"))
        self.assertFalse(contains_cjk("incident notification"))

    def test_index_contains_bigrams_and_trigrams(self):
        terms = cjk_ngrams("障害通知")
        self.assertEqual(terms, ["障害", "害通", "通知", "障害通", "害通知"])

    def test_query_uses_trigrams_for_contiguous_phrase(self):
        self.assertEqual(expand_cjk_query("VPN 障害通知"), "vpn 障害通 害通知")
        self.assertEqual(expand_cjk_query("障害"), "障害")

    def test_ngram_terms_make_japanese_substrings_searchable(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute(
            "CREATE VIRTUAL TABLE documents USING fts5(content, cjk_terms, "
            'tokenize="unicode61 remove_diacritics 2")'
        )
        connection.execute(
            "INSERT INTO documents VALUES (?, ?)",
            (
                "パスワード変更時に障害通知を確認します",
                cjk_index_terms("パスワード変更時に障害通知を確認します"),
            ),
        )

        for query in ("パスワード", "変更", "障害通知"):
            terms = expand_cjk_query(query).split()
            fts_query = " ".join(f'"{term}"' for term in terms)
            count = connection.execute(
                "SELECT COUNT(*) FROM documents WHERE documents MATCH ?", (fts_query,)
            ).fetchone()[0]
            self.assertEqual(count, 1, query)


class TestIndexFieldDetection(unittest.TestCase):
    """An index built before `cjk_terms` existed must be detected as stale.

    FT.INFO only reports the document count, which stays correct across schema
    changes; without looking at the attributes an upgraded site keeps serving
    an index that cannot match CJK queries.
    """

    def test_flat_attributes_with_identifier(self):
        attributes = [
            ["identifier", "subject", "attribute", "subject", "type", "TEXT"],
            ["identifier", "description", "attribute", "description", "type", "TEXT"],
        ]
        self.assertEqual(
            indexed_field_names(attributes), {"subject", "description"}
        )

    def test_bytes_and_mapping_attributes(self):
        attributes = [
            [b"identifier", b"subject", b"type", b"TEXT"],
            {"identifier": "cjk_terms", "type": "TEXT"},
        ]
        self.assertEqual(indexed_field_names(attributes), {"subject", "cjk_terms"})

    def test_legacy_flat_attributes_without_identifier(self):
        self.assertEqual(
            indexed_field_names([["subject", "type", "TEXT"]]), {"subject"}
        )

    def test_missing_field_is_visible(self):
        old_index = indexed_field_names(
            [["identifier", "subject"], ["identifier", "description"]]
        )
        wanted = {"subject", "description", "cjk_terms"}
        self.assertFalse(wanted <= old_index)

    def test_unknown_shape_returns_empty(self):
        # Empty means "cannot tell"; callers must not rebuild on that basis.
        self.assertEqual(indexed_field_names(None), set())
        self.assertEqual(indexed_field_names([42]), set())


if __name__ == "__main__":
    unittest.main()
