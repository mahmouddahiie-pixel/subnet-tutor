"""Comprehensive pre-submission sanity checks for Subnet Tutor."""

from __future__ import annotations

import ipaddress
import json
import math
import re
import unittest
import unittest.mock
from pathlib import Path

from app.game.scenarios import (
    _borrowed_bits_for_subnets,
    _host_bits_for_hosts,
    _subnet_solution,
    generate_assignment_scenario,
    generate_scenario,
    grade_subnet_answer,
)
from app.i18n import get_strings
from app.llm.client import ask_tutor, generate_fallback_response, is_model_available
from app.main import create_app
from app.rag.retriever import build_index, load_documents, retrieve
from app.tutorial.finger_lessons import load_finger_table, validate_walkthrough

ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = ROOT / "app" / "i18n"
POWERS_PATH = ROOT / "knowledge" / "powers_of_two.json"


class TestDeterministicCalculations(unittest.TestCase):
    def test_borrowed_bits_minimum_subnets(self):
        self.assertEqual(_borrowed_bits_for_subnets(2), 1)
        self.assertEqual(_borrowed_bits_for_subnets(4), 2)
        self.assertEqual(_borrowed_bits_for_subnets(8), 3)
        self.assertEqual(_borrowed_bits_for_subnets(6), 3)

    def test_host_bits_requirements(self):
        for hosts in (25, 50, 100):
            bits = _host_bits_for_hosts(hosts)
            usable = 2**bits - 2
            self.assertGreaterEqual(usable, hosts)

    def test_subnet_solution_matches_ipaddress(self):
        network = "192.168.1.0/24"
        for required in (2, 4, 6, 8, 10, 16):
            borrowed = _borrowed_bits_for_subnets(required)
            solution = _subnet_solution(network, borrowed)
            net = ipaddress.IPv4Network(network, strict=False)
            new_prefix = net.prefixlen + borrowed
            subnets = list(net.subnets(new_prefix=new_prefix))
            self.assertEqual(solution["answer_prefix"], new_prefix)
            self.assertEqual(solution["answer_subnets"], 2**borrowed)
            self.assertEqual(solution["answer_mask"], str(subnets[0].netmask))
            self.assertEqual(len(subnets), solution["answer_subnets"])
            self.assertLessEqual(len(solution["subnet_list"]), 8)

    def test_host_count_scenario_prefix(self):
        scenario = generate_scenario(2, seed=42)
        net = ipaddress.IPv4Network(scenario["network"], strict=False)
        new_prefix = scenario["answer_prefix"]
        host_bits = 32 - new_prefix
        usable = 2**host_bits - 2 if host_bits > 1 else 0
        self.assertGreaterEqual(usable, scenario["required_value"])

    def test_grade_all_answer_fields(self):
        scenario = generate_scenario(1, seed=7)
        correct = {
            "prefix": scenario["answer_prefix"],
            "subnets": scenario["answer_subnets"],
            "block_size": scenario["answer_block_size"],
            "mask": scenario["answer_mask"],
            "fingers": scenario["borrowed_bits"],
        }
        self.assertTrue(grade_subnet_answer(scenario, correct)["correct"])

    def test_grade_rejects_wrong_values(self):
        scenario = generate_scenario(1, seed=7)
        for field, wrong in [
            ("prefix", scenario["answer_prefix"] + 1),
            ("subnets", scenario["answer_subnets"] + 1),
            ("block_size", scenario["answer_block_size"] + 1),
            ("fingers", scenario["borrowed_bits"] + 1),
        ]:
            answer = {"prefix": scenario["answer_prefix"], "fingers": scenario["borrowed_bits"]}
            answer[field] = wrong
            self.assertFalse(grade_subnet_answer(scenario, answer)["correct"], field)


class TestIpSyntaxHandling(unittest.TestCase):
    def test_invalid_prefix_rejected(self):
        scenario = generate_scenario(1, seed=1)
        result = grade_subnet_answer(scenario, {"prefix": "abc"})
        self.assertFalse(result["correct"])
        self.assertTrue(any("prefix" in d.lower() for d in result["details"]))

    def test_prefix_with_slash_accepted(self):
        scenario = generate_scenario(1, seed=1)
        result = grade_subnet_answer(
            scenario, {"prefix": f"/{scenario['answer_prefix']}"}
        )
        self.assertTrue(result["correct"])

    def test_invalid_mask_rejected(self):
        scenario = generate_scenario(1, seed=1)
        for bad_mask in ("999.999.999.999", "not-a-mask", "255.255.255"):
            result = grade_subnet_answer(scenario, {"mask": bad_mask})
            self.assertFalse(result["correct"])
            self.assertTrue(any("mask" in d.lower() or "invalid" in d.lower() for d in result["details"]))

    def test_valid_mask_dotted_decimal(self):
        scenario = generate_scenario(1, seed=1)
        result = grade_subnet_answer(scenario, {"mask": scenario["answer_mask"]})
        self.assertTrue(result["correct"])

    def test_subnet_list_boundaries(self):
        scenario = generate_scenario(1, seed=55)
        net = ipaddress.IPv4Network(scenario["network"], strict=False)
        all_subnets = list(net.subnets(new_prefix=scenario["answer_prefix"]))
        listed = scenario["subnet_list"]
        self.assertLessEqual(len(listed), 8)
        self.assertLessEqual(len(listed), len(all_subnets))
        for s in listed:
            ipaddress.IPv4Network(s, strict=False)

    def test_assignment_subnet_contains_devices(self):
        for seed in range(10):
            scenario = generate_assignment_scenario(seed=seed)
            target = ipaddress.IPv4Network(scenario["answer_subnet"], strict=False)
            for device in scenario["devices"]:
                ip = ipaddress.IPv4Address(device["ip"])
                self.assertIn(ip, target)


class TestFingerInteractions(unittest.TestCase):
    def test_finger_table_matches_powers_json(self):
        table = load_finger_table()
        raw = json.loads(POWERS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(table), 8)
        self.assertEqual(table, raw)

    def test_finger_to_subnet_mapping(self):
        table = load_finger_table()
        for row in table:
            self.assertEqual(row["subnets"], 2 ** row["finger"])

    def test_walkthrough_three_fingers_six_subnets(self):
        result = validate_walkthrough(3, required_subnets=6)
        self.assertTrue(result["valid"])
        self.assertEqual(result["subnets"], 8)
        self.assertEqual(result["new_prefix"], 27)
        self.assertEqual(result["block_size"], 32)
        self.assertEqual(result["message_key"], "walkthrough_correct")
        self.assertEqual(result["left_fingers"], 3)
        self.assertEqual(result["right_fingers"], 0)

    def test_walkthrough_hand_split_at_six_fingers(self):
        result = validate_walkthrough(6, required_subnets=6)
        self.assertTrue(result["valid"])
        self.assertEqual(result["subnets"], 64)
        self.assertEqual(result["left_fingers"], 5)
        self.assertEqual(result["right_fingers"], 1)
        self.assertEqual(result["message_key"], "walkthrough_correct")

    def test_walkthrough_left_hand_progress(self):
        result = validate_walkthrough(2, required_subnets=6)
        self.assertFalse(result["valid"])
        self.assertEqual(result["subnets"], 4)
        self.assertEqual(result["message_key"], "walkthrough_left_progress")
        self.assertEqual(result["left_fingers"], 2)
        self.assertEqual(result["right_fingers"], 0)

    def test_hand_finger_count_mapping(self):
        """Mirror JS handFingerCounts: 1-5 left only, 6-8 left full + right."""
        cases = [
            (0, 0, 0),
            (1, 1, 0),
            (5, 5, 0),
            (6, 5, 1),
            (8, 5, 3),
        ]
        for fingers, left, right in cases:
            result = validate_walkthrough(fingers, required_subnets=999)
            if fingers == 0:
                self.assertFalse(result["valid"])
                continue
            self.assertEqual(result["left_fingers"], left, f"fingers={fingers}")
            self.assertEqual(result["right_fingers"], right, f"fingers={fingers}")

    def test_walkthrough_invalid_finger_count(self):
        result = validate_walkthrough(0, required_subnets=6)
        self.assertFalse(result["valid"])
        result = validate_walkthrough(9, required_subnets=6)
        self.assertFalse(result["valid"])


class TestLanguages(unittest.TestCase):
    def test_locale_files_load(self):
        en = get_strings("en")
        ar = get_strings("ar")
        self.assertTrue(en["app_title"])
        self.assertTrue(ar["app_title"])

    def test_all_template_keys_in_both_locales(self):
        en = json.loads((I18N_DIR / "en.json").read_text(encoding="utf-8"))
        ar = json.loads((I18N_DIR / "ar.json").read_text(encoding="utf-8"))
        self.assertEqual(set(en.keys()), set(ar.keys()))

    def test_game_prompt_templates_format(self):
        for lang in ("en", "ar"):
            strings = get_strings(lang)
            for key in (
                "game_level1_prompt",
                "game_level2_prompt",
                "game_level3_prompt",
                "game_level4_prompt",
            ):
                formatted = strings[key].format(network="192.168.1.0/24", required=6)
                self.assertIn("192.168.1.0/24", formatted)
                self.assertIn("6", formatted)

    def test_arabic_rag_chunks_retrievable(self):
        build_index(force=True)
        context = retrieve("طريقة الأصابع subnetting", language="ar")
        self.assertTrue(context)
        docs = load_documents()
        ar_docs = [d for d in docs if d["metadata"].get("lang") == "ar"]
        self.assertGreater(len(ar_docs), 0)

    def test_arabic_home_page_shows_translated_text(self):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/api/language", json={"lang": "ar"})
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("الرئيسية", html)
        self.assertIn("معلّم", html)
        self.assertIn("ابدأ الدرس", html)
        self.assertNotIn("Start Tutorial", html)
        self.assertNotIn("Finger counting, paper-fold", html)

    def test_arabic_tutorial_page_shows_translated_text(self):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/api/language", json={"lang": "ar"})
        resp = client.get("/tutorial")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("الأصابع", html)
        self.assertIn("القناع (البايت الرابع)", html)
        self.assertNotIn("Mask (4th octet)", html)
        self.assertNotIn("Ask the tutor", html)

    def test_arabic_templates_avoid_common_hardcoded_english(self):
        """Ensure key user-visible English phrases are not left in AR page responses."""
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/api/language", json={"lang": "ar"})
        forbidden = [
            "LLM ready",
            "Tutor fallback mode",
            "Finger counting",
            "AI Tutor",
            "Fold → Split",
            "Mask (4th octet)",
            "Ask the tutor",
            "Tap Raise Fingers",
        ]
        for path in ("/", "/tutorial", "/game?level=1"):
            html = client.get(path).data.decode("utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, html, f"{phrase!r} found on {path}")


class TestOfflineLlmLogic(unittest.TestCase):
    def test_is_model_available_when_gguf_exists(self):
        model_path = ROOT / "model" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        if model_path.is_file():
            self.assertTrue(is_model_available())
        else:
            self.assertFalse(is_model_available())

    def test_fallback_mode_when_model_missing(self):
        answer = generate_fallback_response(
            "What is /27?",
            "context text",
            language="en",
            model_available=False,
        )
        self.assertIn("Offline mode", answer)
        self.assertIn("download_model.sh", answer)
        self.assertIn("•", answer)

    def test_fallback_mode_when_model_loading(self):
        answer = generate_fallback_response(
            "What is /27?",
            "- Subnets created = 2^borrowed_bits\n- Block size = 32",
            language="en",
            model_loading=True,
            model_available=True,
        )
        self.assertIn("Model is loading", answer)
        self.assertIn("LLM ready", answer)
        self.assertNotIn("download_model.sh", answer)

    def test_fallback_mode_when_model_load_failed(self):
        answer = generate_fallback_response(
            "What is /27?",
            "- Subnets created = 2^borrowed_bits",
            language="en",
            model_available=True,
            model_load_error="No module named 'llama_cpp'",
        )
        self.assertIn("Model failed to load", answer)
        self.assertIn("llama_cpp", answer)
        self.assertNotIn("Model is loading", answer)

    def test_fallback_arabic_uses_arabic_text(self):
        answer = generate_fallback_response(
            "ما هو /27؟",
            "- Subnets = 2^borrowed_bits",
            language="ar",
            model_available=True,
        )
        self.assertIn("【المعلّم الذكي】", answer)
        self.assertIn("سؤالك:", answer)

    def test_ask_tutor_uses_rag_context_in_prompt(self):
        build_index(force=True)
        context = retrieve("finger method 3 subnets", language="en")
        with unittest.mock.patch("app.llm.client.is_model_available", return_value=False):
            result = ask_tutor("How many fingers for 6 subnets?", context, language="en")
        self.assertEqual(result["mode"], "fallback")
        self.assertIn("•", result["answer"])
        self.assertNotIn("Retrieved context:", result["answer"])


class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        self.model_patch = unittest.mock.patch(
            "app.llm.client.is_model_available", return_value=False
        )
        self.model_patch.start()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.model_patch.stop()

    def test_home_and_tutorial(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/tutorial").status_code, 200)

    def test_game_levels(self):
        for level in range(1, 5):
            resp = self.client.get(f"/game?level={level}")
            self.assertEqual(resp.status_code, 200, f"level {level}")

    def test_language_switch_and_rtl(self):
        self.client.post("/api/language", json={"lang": "ar"})
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'dir="rtl"', resp.data)

        self.client.post("/api/language", json={"lang": "en"})
        resp = self.client.get("/")
        self.assertIn(b'dir="ltr"', resp.data)

    def test_tutorial_validate_api(self):
        resp = self.client.post(
            "/api/tutorial/validate",
            json={"fingers": 3, "required_subnets": 6},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["new_prefix"], 27)

    def test_game_grade_api(self):
        scenario = generate_scenario(1, seed=99)
        resp = self.client.post(
            "/api/game/grade",
            json={
                "scenario": scenario,
                "answer": {
                    "fingers": scenario["borrowed_bits"],
                    "prefix": scenario["answer_prefix"],
                },
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["correct"])

    def test_explain_api(self):
        import time

        start = time.monotonic()
        resp = self.client.post(
            "/api/explain",
            json={"question": "Why use 3 fingers for 6 subnets on /24?"},
        )
        elapsed = time.monotonic() - start
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("answer", data)
        self.assertIn("mode", data)
        self.assertEqual(data["mode"], "fallback")
        self.assertLess(elapsed, 2.0, f"explain took {elapsed:.2f}s — should be fast RAG path")

    def test_explain_api_use_llm_flag(self):
        from app.llm.client import ask_tutor

        result = ask_tutor("test question", "subnet context", language="en", use_llm=False)
        self.assertEqual(result["mode"], "fallback")
        self.assertIn("answer", result)

    def test_game_hint_api(self):
        scenario = generate_scenario(1, seed=5)
        resp = self.client.post(
            "/api/game/hint",
            json={"scenario": scenario},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("answer", data)
        self.assertIn("mode", data)


if __name__ == "__main__":
    unittest.main()
