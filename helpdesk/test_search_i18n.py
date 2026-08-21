import sqlite3
import unittest

from helpdesk.search_i18n import (
    cjk_index_terms,
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


if __name__ == "__main__":
    unittest.main()
