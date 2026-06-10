import unittest

from evidence_answerer import answer_question


class EvidenceAnswererPublicTests(unittest.TestCase):
    def test_answers_from_trusted_fact_with_citation(self):
        result = answer_question(
            "What is release date?",
            [
                {"id": "doc-1", "text": "Fact: release date = 2026-08-15"},
                {"id": "doc-2", "text": "This paragraph is not a fact."},
            ],
        )

        self.assertEqual(
            result,
            {"status": "answered", "answer": "2026-08-15", "citations": ["doc-1"]},
        )

    def test_returns_insufficient_evidence_without_matching_fact(self):
        result = answer_question(
            "What is owner?",
            [{"id": "doc-1", "text": "Fact: release date = 2026-08-15"}],
        )

        self.assertEqual(result, {"status": "insufficient_evidence", "answer": None, "citations": []})


if __name__ == "__main__":
    unittest.main()
