"""End-to-end deployment readiness checks via Flask test_client."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
import unittest.mock
from pathlib import Path

from app.game.scenarios import generate_scenario
from app.i18n import get_strings
from app.llm.client import ask_tutor, is_model_available
from app.main import create_app
from app.rag.retriever import build_index, retrieve
from app.tutorial.finger_lessons import get_lesson_steps, load_finger_table

ROOT = Path(__file__).resolve().parents[1]


class E2EReadinessBase(unittest.TestCase):
    def setUp(self):
        self.model_patch = unittest.mock.patch(
            "app.llm.client.is_model_available", return_value=is_model_available()
        )
        self.model_patch.start()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.model_patch.stop()

    def html(self, path: str) -> str:
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200, path)
        return resp.data.decode("utf-8")


class TestHomePage(E2EReadinessBase):
    def test_logo_title_keith_barker_en(self):
        html = self.html("/")
        self.assertIn("Keith Barker Method", html)
        self.assertIn("Start Tutorial", html)
        self.assertIn("Play Game", html)

    def test_nav_links_present(self):
        html = self.html("/")
        for href in ('href="/"', 'href="/tutorial"', 'href="/game"'):
            self.assertIn(href, html)

    def test_feature_cards_render(self):
        html = self.html("/")
        self.assertIn("Finger Counting Method", html)
        self.assertIn("Subnetting Challenge", html)
        self.assertIn("Explain with AI Tutor", html)

    def test_language_switch_buttons(self):
        html = self.html("/")
        self.assertIn('data-lang="en"', html)
        self.assertIn('data-lang="ar"', html)

    def test_start_buttons_link_correctly(self):
        html = self.html("/")
        self.assertIn('href="/tutorial"', html)
        self.assertIn('href="/game"', html)


class TestTutorialPage(E2EReadinessBase):
    def test_four_step_tabs(self):
        html = self.html("/tutorial")
        tabs = re.findall(r'class="step-tab[^"]*" data-step="(\d+)"', html)
        self.assertEqual(len(tabs), 4)
        self.assertEqual(sorted(tabs), ["0", "1", "2", "3"])

    def test_raise_and_reset_buttons(self):
        html = self.html("/tutorial")
        self.assertGreaterEqual(html.count("Raise Fingers"), 2)
        self.assertGreaterEqual(html.count("Reset"), 2)

    def test_finger_table_rows(self):
        html = self.html("/tutorial")
        rows = html.count("<tr>")
        self.assertGreaterEqual(rows, 9)  # header + 8 data rows

    def test_prev_next_navigation(self):
        html = self.html("/tutorial")
        self.assertIn('id="prev-step"', html)
        self.assertIn('id="next-step"', html)

    def test_explain_buttons_per_step(self):
        html = self.html("/tutorial")
        self.assertEqual(html.count("explain-btn"), 4)

    def test_fold_interactive_present(self):
        html = self.html("/tutorial")
        self.assertIn('id="fold-btn"', html)
        self.assertIn('id="network-bar"', html)

    def test_walkthrough_section(self):
        html = self.html("/tutorial")
        self.assertIn("walkthrough-feedback", html)
        self.assertIn("WALKTHROUGH", html)

    def test_arabic_rtl_on_tutorial(self):
        self.client.post("/api/language", json={"lang": "ar"})
        html = self.html("/tutorial")
        self.assertIn('dir="rtl"', html)
        self.assertIn("الأصابع", html)


class TestGamePage(E2EReadinessBase):
    def test_all_level_tabs(self):
        for level in range(1, 5):
            html = self.html(f"/game?level={level}")
            for lv in range(1, 5):
                self.assertIn(f"/game?level={lv}", html)
            self.assertIn(f"Level {level}", html)

    def test_scenario_embedded_in_page(self):
        html = self.html("/game?level=1")
        self.assertIn("scenario-data", html)
        match = re.search(
            r'<script id="scenario-data" type="application/json">(.+?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        scenario = json.loads(match.group(1))
        self.assertIn("network", scenario)

    def test_submit_and_hint_buttons(self):
        html = self.html("/game?level=1")
        self.assertIn('id="submit-game"', html)
        self.assertIn('id="hint-game"', html)

    def test_arabic_game_prompt(self):
        self.client.post("/api/language", json={"lang": "ar"})
        html = self.html("/game?level=1")
        self.assertIn("الشبكة", html)
        self.assertNotIn("Network:", html)


class TestGameApiFlows(E2EReadinessBase):
    def test_correct_answer_updates_score_and_streak(self):
        scenario = generate_scenario(1, seed=42)
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
        data = resp.get_json()
        self.assertTrue(data["correct"])
        self.assertGreater(data["score"], 0)
        self.assertEqual(data["streak"], 1)

    def test_incorrect_answer_resets_streak(self):
        scenario = generate_scenario(1, seed=42)
        self.client.post(
            "/api/game/grade",
            json={
                "scenario": scenario,
                "answer": {
                    "fingers": scenario["borrowed_bits"],
                    "prefix": scenario["answer_prefix"],
                },
            },
        )
        resp = self.client.post(
            "/api/game/grade",
            json={"scenario": scenario, "answer": {"fingers": 1, "prefix": 32}},
        )
        data = resp.get_json()
        self.assertFalse(data["correct"])
        self.assertEqual(data["streak"], 0)

    def test_badge_awarded_on_first_correct(self):
        scenario = generate_scenario(1, seed=77)
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
        data = resp.get_json()
        self.assertIn("First Success", data.get("badges", []))


class TestAllApis(E2EReadinessBase):
    def test_post_language(self):
        resp = self.client.post("/api/language", json={"lang": "ar"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["lang"], "ar")

    def test_get_model_status(self):
        resp = self.client.get("/api/model-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        for key in ("available", "loaded", "loading", "status", "model_path"):
            self.assertIn(key, data)
        if (ROOT / "model" / "qwen2.5-1.5b-instruct-q4_k_m.gguf").is_file():
            self.assertTrue(data["available"])

    def test_get_finger_table(self):
        resp = self.client.get("/api/finger-table")
        self.assertEqual(resp.status_code, 200)
        table = resp.get_json()
        self.assertEqual(len(table), 8)
        self.assertEqual(table, load_finger_table())

    def test_explain_requires_question(self):
        resp = self.client.post("/api/explain", json={})
        self.assertEqual(resp.status_code, 400)

    def test_explain_fast_fallback(self):
        import time

        start = time.monotonic()
        resp = self.client.post(
            "/api/explain",
            json={"question": "How many subnets with 3 fingers on /24?"},
        )
        elapsed = time.monotonic() - start
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn(data["mode"], ("fallback", "llm"))
        self.assertIn("•", data["answer"])
        self.assertNotIn("Retrieved context:", data["answer"])
        self.assertLess(elapsed, 3.0)

    def test_tutorial_validate_walkthrough(self):
        resp = self.client.post(
            "/api/tutorial/validate",
            json={"fingers": 3, "required_subnets": 6},
        )
        data = resp.get_json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["left_fingers"], 3)
        self.assertEqual(data["right_fingers"], 0)

    def test_game_hint_returns_answer(self):
        scenario = generate_scenario(2, seed=11)
        resp = self.client.post("/api/game/hint", json={"scenario": scenario})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("answer", data)
        self.assertIn("mode", data)


class TestLlmAndRag(E2EReadinessBase):
    def test_rag_retrieve_en_and_ar(self):
        build_index(force=True)
        en_ctx = retrieve("finger method subnetting powers of two", language="en")
        ar_ctx = retrieve("طريقة الأصابع subnetting", language="ar")
        self.assertTrue(en_ctx)
        self.assertTrue(ar_ctx)

    def test_ask_tutor_fallback_readable(self):
        build_index(force=True)
        ctx = retrieve("3 fingers subnets", language="en")
        with unittest.mock.patch("app.llm.client.is_model_loaded", return_value=False):
            result = ask_tutor("How many subnets with 3 fingers?", ctx, language="en")
        self.assertEqual(result["mode"], "fallback")
        self.assertIn("•", result["answer"])
        self.assertNotIn("Retrieved context:", result["answer"])

    def test_ask_tutor_use_llm_when_loaded(self):
        with unittest.mock.patch("app.llm.client.is_model_loaded", return_value=True):
            with unittest.mock.patch(
                "app.llm.client.generate_response", return_value="Mock LLM answer"
            ):
                result = ask_tutor("test", "context", language="en", use_llm=True)
        self.assertEqual(result["mode"], "llm")
        self.assertEqual(result["answer"], "Mock LLM answer")


class TestAdtcSubmission(E2EReadinessBase):
    def test_validate_submission_script(self):
        result = subprocess.run(
            ["bash", "validate_submission.sh"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_metadata_complete(self):
        meta = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["domain"], "math_scientific_reasoning")
        self.assertIn("en", meta["language_scope"])
        self.assertIn("ar", meta["language_scope"])
        self.assertEqual(len(meta["test_prompts"]), 2)
        self.assertIn("model_path", meta["_runtime"])

    def test_download_model_script_idempotent(self):
        result = subprocess.run(
            ["bash", "download_model.sh"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (ROOT / "model" / "qwen2.5-1.5b-instruct-q4_k_m.gguf").is_file()
        )

    def test_report_md_exists(self):
        self.assertTrue((ROOT / "REPORT.md").is_file())

    def test_offline_app_code_no_external_urls(self):
        """Runtime inference must not call external hosts (localhost dev prints are OK)."""
        import_patterns = [
            re.compile(r"\bimport requests\b"),
            re.compile(r"\bfrom requests\b"),
            re.compile(r"urllib\.request"),
            re.compile(r"\bimport httpx\b"),
        ]
        for py_file in (ROOT / "app").rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pat in import_patterns:
                self.assertIsNone(
                    pat.search(text),
                    f"{py_file.relative_to(ROOT)} imports network client",
                )
            bad_urls = []
            for match in re.finditer(r"https?://[^\s\"']+", text):
                url = match.group()
                if any(token in url for token in ("127.0.0.1", "localhost", "{host}")):
                    continue
                bad_urls.append(url)
            self.assertEqual(
                bad_urls,
                [],
                f"{py_file.relative_to(ROOT)} references external URLs: {bad_urls}",
            )

    def test_static_assets_referenced(self):
        for asset in (
            "static/css/style.css",
            "static/js/app.js",
            "static/js/tutorial.js",
            "static/js/game.js",
        ):
            self.assertTrue((ROOT / asset).is_file(), asset)

    def test_lesson_steps_count(self):
        self.assertEqual(len(get_lesson_steps("en")), 4)
        self.assertEqual(len(get_lesson_steps("ar")), 4)


if __name__ == "__main__":
    unittest.main()
