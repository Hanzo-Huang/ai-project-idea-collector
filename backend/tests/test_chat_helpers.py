import unittest

from app.services.chat import clean_history, direct_answer


class ChatHelperTests(unittest.TestCase):
    def test_greeting_is_answered_without_project_context(self):
        answer = direct_answer("Hi")

        self.assertIsNotNone(answer)
        self.assertIn("collected AI projects", answer)

    def test_identity_is_answered_without_project_context(self):
        answer = direct_answer("Who are you?")

        self.assertIsNotNone(answer)
        self.assertIn("AI Project Idea Collector assistant", answer)

    def test_project_query_uses_rag_path(self):
        self.assertIsNone(direct_answer("Find edge AI projects using YOLO"))

    def test_history_is_limited_to_valid_chat_messages(self):
        history = [
            {"role": "system", "content": "ignore me"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "tool", "content": "ignore me"},
            {"role": "assistant", "content": ""},
        ]

        self.assertEqual(clean_history(history), [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
