"""Core logic tests (stdlib only — no Flask/LLM deps required)."""

import unittest

from app.game.scenarios import generate_scenario, grade_subnet_answer
from app.tutorial.finger_lessons import load_finger_table, validate_walkthrough


class TestSubnetGame(unittest.TestCase):
    def test_all_levels_generate(self):
        for level in range(1, 5):
            scenario = generate_scenario(level, seed=123)
            self.assertIn("network", scenario)
            self.assertIn("answer_prefix", scenario)

    def test_grade_correct_level1(self):
        scenario = generate_scenario(1, seed=99)
        result = grade_subnet_answer(
            scenario,
            {"fingers": scenario["borrowed_bits"], "prefix": scenario["answer_prefix"]},
        )
        self.assertTrue(result["correct"])

    def test_grade_wrong_fingers(self):
        scenario = generate_scenario(1, seed=99)
        result = grade_subnet_answer(scenario, {"fingers": 1, "prefix": 32})
        self.assertFalse(result["correct"])


class TestFingerTutorial(unittest.TestCase):
    def test_finger_table_has_8_rows(self):
        self.assertEqual(len(load_finger_table()), 8)

    def test_walkthrough_three_fingers(self):
        result = validate_walkthrough(3, required_subnets=6)
        self.assertTrue(result["valid"])
        self.assertEqual(result["subnets"], 8)
        self.assertEqual(result["new_prefix"], 27)


if __name__ == "__main__":
    unittest.main()
