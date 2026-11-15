"""The recommendation policy, against the classifier's real answer shape.

The fixtures are trimmed copies of live `nerve_assess` envelopes (jev-1.14.0 over
typesafe-system-one): one typed choice question per option, probabilities per label.
"""

from __future__ import annotations

import json
import unittest

import recommend

TAKE = recommend.TAKE_NOW


def envelope(*take_now: float, ok: bool = True) -> str:
    """A dispatch result with one q1..qN answer per probability."""
    answers = {}
    for index, probability in enumerate(take_now):
        rest = round((1.0 - probability) / 2, 3)
        answers["q%d" % (index + 1)] = {
            "choice": TAKE if probability >= 0.5 else recommend.LATER,
            "confidence": probability,
            "probabilities": {TAKE: probability, recommend.LATER: rest, recommend.SKIP: rest},
            "type": "choice",
        }
    return json.dumps({"answers": answers, "contract": "assess/v1", "ok": ok})


def dispatcher(result, log=None):
    def dispatch(name, args):
        if log is not None:
            log.append((name, args))
        if isinstance(result, Exception):
            raise result
        return result

    return dispatch


class QuestionsTest(unittest.TestCase):
    def test_one_typed_choice_per_option(self):
        questions = recommend.questions(["Push it", "Tag it"])
        self.assertEqual(sorted(questions), ["q1", "q2"])
        self.assertEqual(questions["q1"]["type"], "choice")
        self.assertEqual(sorted(questions["q1"]["criteria"]), sorted([TAKE, recommend.LATER, recommend.SKIP]))
        self.assertIn("Push it", questions["q1"]["instructions"])
        self.assertIn("Tag it", questions["q2"]["instructions"])

    def test_each_question_owns_its_criteria_copy(self):
        questions = recommend.questions(["A", "B"])
        questions["q1"]["criteria"][TAKE] = "edited"
        self.assertNotEqual(questions["q2"]["criteria"][TAKE], "edited")


class PicksTest(unittest.TestCase):
    def test_several_can_clear_the_bar_together(self):
        answers = json.loads(envelope(0.81, 0.79, 0.77))["answers"]
        self.assertEqual(recommend.picks(answers, 3), [0, 1, 2])

    def test_a_clear_winner_gets_one(self):
        answers = json.loads(envelope(0.91, 0.04, 0.04, 0.01))["answers"]
        self.assertEqual(recommend.picks(answers, 4), [0])

    def test_nothing_clears_the_bar(self):
        answers = json.loads(envelope(0.4, 0.35, 0.25))["answers"]
        self.assertEqual(recommend.picks(answers, 3), [])

    def test_the_cap_keeps_the_strongest_three(self):
        answers = json.loads(envelope(0.52, 0.9, 0.61, 0.88))["answers"]
        self.assertEqual(recommend.picks(answers, 4), [1, 2, 3])

    def test_missing_or_malformed_answers_are_skipped_not_guessed(self):
        answers = {"q1": {"probabilities": {TAKE: 0.9}}, "q2": {"probabilities": "nope"}, "q3": {}}
        self.assertEqual(recommend.picks(answers, 3), [0])
        self.assertEqual(recommend.picks({}, 3), [])
        self.assertEqual(recommend.picks(answers, 0), [])

    def test_a_boolean_is_not_a_probability(self):
        answers = {"q1": {"probabilities": {TAKE: True}}}
        self.assertEqual(recommend.picks(answers, 1), [])


class ReplyTest(unittest.TestCase):
    def test_the_attribute_is_ready_to_copy(self):
        answers = json.loads(envelope(0.81, 0.2, 0.77))["answers"]
        text = recommend.reply(["A", "B", "C"], answers)
        self.assertIn('rec="1,3"', text)
        self.assertIn("2 of 3", text)
        self.assertIn("0.81", text)

    def test_no_recommendation_says_so_plainly(self):
        answers = json.loads(envelope(0.3, 0.3))["answers"]
        self.assertIn("leave rec out", recommend.reply(["A", "B"], answers))


class RecommendTest(unittest.TestCase):
    def test_calls_the_classifier_with_the_options_and_context(self):
        log = []
        text = recommend.recommend(dispatcher(envelope(0.9, 0.2), log), ["Push it", "Tag it"], "Apo asked for a review.")
        self.assertEqual(log[0][0], "nerve_assess")
        self.assertEqual(log[0][1]["state"], "Apo asked for a review.")
        self.assertEqual(sorted(log[0][1]["questions"]), ["q1", "q2"])
        self.assertIn('rec="1"', text)

    def test_a_missing_classifier_falls_through_to_the_older_name(self):
        calls = []

        def dispatch(name, args):
            calls.append(name)
            if name == "nerve_assess":
                raise RuntimeError("unknown tool")
            return envelope(0.75, 0.75)

        text = recommend.recommend(dispatch, ["A", "B"])
        self.assertEqual(calls, ["nerve_assess", "jev_assess"])
        self.assertIn('rec="1,2"', text)

    def test_no_classifier_at_all_leaves_the_directive_alone(self):
        text = recommend.recommend(dispatcher(RuntimeError("no such tool")), ["A", "B"])
        self.assertIn("leave rec out", text)
        self.assertNotIn('rec="', text)

    def test_an_error_envelope_is_not_a_verdict(self):
        text = recommend.recommend(dispatcher(envelope(0.9, 0.9, ok=False)), ["A", "B"])
        self.assertIn("leave rec out", text)

    def test_junk_instead_of_json_is_ignored(self):
        self.assertIn("leave rec out", recommend.recommend(dispatcher("<html>502</html>"), ["A", "B"]))

    def test_two_options_are_the_floor(self):
        self.assertIn("at least two options", recommend.recommend(dispatcher(envelope(0.9)), ["Only one"]))


class HandlerTest(unittest.TestCase):
    def test_options_from_a_params_dict(self):
        handler = recommend.handler(dispatcher(envelope(0.9, 0.1)))
        self.assertIn('rec="1"', handler({"options": ["Push it", "Tag it"], "context": "reviewed a diff"}))

    def test_options_given_as_newline_text(self):
        handler = recommend.handler(dispatcher(envelope(0.9, 0.9)))
        self.assertIn('rec="1,2"', handler({"options": "Push it\nTag it"}))

    def test_missing_options_answers_with_an_instruction(self):
        handler = recommend.handler(dispatcher(envelope(0.9, 0.9)))
        self.assertIn("options array", handler({}))

    def test_six_options_is_the_ceiling(self):
        log = []
        handler = recommend.handler(dispatcher(envelope(0.9, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2), log))
        handler({"options": ["A", "B", "C", "D", "E", "F", "G"]})
        self.assertEqual(len(log[0][1]["questions"]), recommend.MAX_OPTIONS)


if __name__ == "__main__":
    unittest.main()
