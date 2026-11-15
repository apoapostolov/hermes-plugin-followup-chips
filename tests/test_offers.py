"""The closing-offer detector: what gets turned into chips, and what is left alone.

Run with `python -m unittest discover -s tests` (or pytest).
"""

from __future__ import annotations

import unittest

import offers


def rewrite(text, platform="local"):
    return offers.rewrite(text, platform=platform)


class ClosingOfferTest(unittest.TestCase):
    def test_bulleted_offer_with_lead_in_becomes_multi_select(self):
        text = (
            "Branch is pushed and the PR is open.\n\n"
            "Want me to take any of these next?\n"
            "- Add a CHANGELOG entry\n"
            "- Wire the new flag into the settings page\n"
            "- Update the docs screenshot"
        )
        out = rewrite(text, platform="local")
        self.assertEqual(
            out,
            "Branch is pushed and the PR is open.\n\n"
            '::followups{multi="1" q1="Add a CHANGELOG entry" '
            'q2="Wire the new flag into the settings page" q3="Update the docs screenshot"}',
        )

    def test_numbered_offer_keeps_item_text_without_the_numbers(self):
        text = "Done.\n\nSay the word and I'll do these:\n1. Bump the version\n2. Tag the release"
        out = rewrite(text, platform="desktop")
        self.assertEqual(out, 'Done.\n\n::followups{multi="1" q1="Bump the version" q2="Tag the release"}')

    def test_single_sentence_offer_drops_the_lead_in(self):
        out = rewrite("Committed the fix.\n\nSay the word and I'll push it and open the PR.")
        self.assertEqual(out, 'Committed the fix.\n\n::followups{q1="Push it and open the PR"}')

    def test_question_form_becomes_an_imperative_option(self):
        out = rewrite("The suite is green.\n\nWant me to run the whole thing again?")
        self.assertEqual(out, 'The suite is green.\n\n::followups{q1="Run the whole thing again"}')

    def test_can_also_offer_is_a_trigger(self):
        out = rewrite("Shipped.\n\nI can also add a changelog entry.")
        self.assertEqual(out, 'Shipped.\n\n::followups{q1="Add a changelog entry"}')

    def test_trailing_qualifier_is_dropped_from_the_option(self):
        out = rewrite("Pushed.\n\nI'll add the changelog entry if you want.")
        self.assertEqual(out, 'Pushed.\n\n::followups{q1="Add the changelog entry"}')

    def test_keeps_prose_that_is_not_the_offer(self):
        out = rewrite(
            "Two tests still fail on Windows.\n\nShall I dig into those first?"
        )
        self.assertEqual(out, 'Two tests still fail on Windows.\n\n::followups{q1="Dig into those first"}')

    def test_quotes_in_an_option_never_break_the_directive(self):
        out = rewrite('Done.\n\nWant me to rename it to "the board"?')
        self.assertEqual(out, "Done.\n\n::followups{q1=\"Rename it to 'the board'\"}")

    def test_caps_the_option_count(self):
        text = "Done.\n\nWant me to:\n" + "\n".join("- Step %d" % i for i in range(1, 10))
        out = rewrite(text)
        self.assertIn('multi="1" q1="Step 1"', out)
        self.assertIn('q6="Step 6"', out)
        self.assertNotIn("q7=", out)


class LeftAloneTest(unittest.TestCase):
    def test_plain_reply_is_untouched(self):
        self.assertIsNone(rewrite("All tests pass. Nothing else needed."))

    def test_statement_of_intent_is_not_an_offer(self):
        self.assertIsNone(rewrite("I'll check the log first."))

    def test_mid_reply_offer_is_left_alone(self):
        self.assertIsNone(rewrite("Want me to push it?\n\nThe log shows a retry."))

    def test_existing_directive_is_not_rewritten(self):
        text = 'Done.\n\n::followups{q1="Push it"}'
        self.assertIsNone(rewrite(text))

    def test_other_surfaces_are_never_rewritten(self):
        self.assertIsNone(rewrite("Done.\n\nWant me to push it?", platform="telegram"))

    def test_conditional_clause_is_not_an_offer(self):
        self.assertIsNone(rewrite("The rule fires if you want strict mode."))

    def test_empty_and_non_string_replies(self):
        self.assertIsNone(rewrite(""))
        self.assertIsNone(rewrite(None))


class DirectiveTest(unittest.TestCase):
    def test_one_option_has_no_multi(self):
        self.assertEqual(offers.directive(["Push it"]), '::followups{q1="Push it"}')

    def test_several_options_are_multi(self):
        self.assertEqual(
            offers.directive(["Push it", "Open the PR"]),
            '::followups{multi="1" q1="Push it" q2="Open the PR"}',
        )


class StampAccentTest(unittest.TestCase):
    """The accent setting rides in the directive: renderer code cannot read settings."""

    def test_it_stamps_a_directive_without_one(self):
        self.assertEqual(
            offers.stamp_accent('::followups{multi="1" q1="A" q2="B"}'),
            '::followups{accent="0" multi="1" q1="A" q2="B"}',
        )

    def test_it_leaves_an_existing_accent_alone(self):
        text = '::followups{accent="1" q1="A"}'
        self.assertEqual(offers.stamp_accent(text), text)
        text = '::followups{accent="0" q1="A"}'
        self.assertEqual(offers.stamp_accent(text), text, "idempotent")

    def test_prose_and_other_text_come_back_unchanged(self):
        for text in ["", None, "No directive here, just prose.", "::blocks{id='x'}"]:
            self.assertEqual(offers.stamp_accent(text), text)

    def test_it_keeps_the_directive_on_its_own_line(self):
        text = "Done.\n\n" + offers.directive(["Push it", "Open the PR"])
        out = offers.stamp_accent(text)
        self.assertTrue(out.startswith("Done.\n\n::followups{accent=\"0\" "))
        self.assertTrue(out.endswith("}"))

    def test_a_value_is_sanitised(self):
        # The value is internal (always "0"), but a stray quote must not break markup.
        self.assertEqual(
            offers.stamp_accent('::followups{q1="A"}', '0" x="1'),
            '::followups{accent="0x1" q1="A"}',
        )
        self.assertEqual(
            offers.stamp_accent('::followups{q1="A"}', '""'),
            '::followups{accent="0" q1="A"}',
            "an empty value falls back to the default",
        )


if __name__ == "__main__":
    unittest.main()
