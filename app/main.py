"""Flask application entry point for Subnet Tutor."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from app.game.scenarios import generate_scenario, grade_subnet_answer
from app.game.scoring import badge_labels, update_score
from app.i18n import get_strings, translate
from app.llm.client import (
    ask_tutor,
    get_model_load_error,
    get_model_status_dict,
    is_model_available,
    is_model_loaded,
    is_model_loading,
    retry_model_preload,
    start_model_preload,
)
from app.rag.retriever import build_index, retrieve
from app.tutorial.finger_lessons import get_lesson_steps, load_finger_table, validate_walkthrough

ROOT = Path(__file__).resolve().parents[1]
STATIC_VERSION = os.environ.get("SUBNET_TUTOR_STATIC_VERSION", "4")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.secret_key = os.environ.get("SUBNET_TUTOR_SECRET", "subnet-tutor-offline-dev-key")

    @app.before_request
    def init_session():
        session.setdefault("lang", "en")
        session.setdefault("score", 0)
        session.setdefault("streak", 0)
        session.setdefault("badges", [])
        session.setdefault("levels_completed", {"1": 0, "2": 0, "3": 0, "4": 0})
        session.setdefault("game_seed", random.randint(1, 99999))

    @app.context_processor
    def inject_i18n():
        lang = session.get("lang", "en")
        strings = get_strings(lang)
        return {
            "t": strings,
            "lang": lang,
            "dir": "rtl" if lang == "ar" else "ltr",
            "model_loaded": is_model_loaded(),
            "model_loading": is_model_loading(),
            "model_error": get_model_load_error(),
            "static_version": STATIC_VERSION,
        }

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/tutorial")
    def tutorial():
        lang = session.get("lang", "en")
        steps = get_lesson_steps(lang)
        finger_table = load_finger_table()
        return render_template("tutorial.html", steps=steps, finger_table=finger_table)

    @app.route("/game")
    def game():
        level = int(request.args.get("level", 1))
        level = max(1, min(4, level))
        seed = session.get("game_seed", 42) + level * 100
        scenario = generate_scenario(level, seed=seed)
        lang = session.get("lang", "en")
        prompt_template = get_strings(lang).get(scenario.get("prompt_key", ""), "")
        prompt = prompt_template.format(
            network=scenario["network"],
            required=scenario.get("required_value", ""),
        )
        return render_template(
            "game.html",
            level=level,
            scenario=scenario,
            prompt=prompt,
            badges=badge_labels(session.get("badges", []), lang),
            score=session.get("score", 0),
            streak=session.get("streak", 0),
        )

    @app.route("/api/language", methods=["POST"])
    def set_language():
        data = request.get_json(silent=True) or {}
        lang = data.get("lang", "en")
        if lang in ("en", "ar"):
            session["lang"] = lang
        return jsonify({"lang": session["lang"]})

    @app.route("/api/model-status")
    def model_status():
        return jsonify(get_model_status_dict())

    @app.route("/api/model-reload", methods=["POST"])
    def model_reload():
        retry_model_preload()
        return jsonify(get_model_status_dict())

    @app.route("/api/explain", methods=["POST"])
    def explain():
        data = request.get_json(silent=True) or {}
        question = data.get("question", "")
        lang = session.get("lang", "en")
        if not question:
            return jsonify({"error": "question required"}), 400

        use_llm = bool(data.get("use_llm", False))
        try:
            build_index()
            context = retrieve(question, language=lang)
            result = ask_tutor(question, context, language=lang, use_llm=use_llm)
            return jsonify(result)
        except Exception as exc:
            return jsonify({"answer": str(exc), "mode": "error"}), 500

    @app.route("/api/tutorial/validate", methods=["POST"])
    def tutorial_validate():
        data = request.get_json(silent=True) or {}
        fingers = int(data.get("fingers", 0))
        required = int(data.get("required_subnets", 6))
        lang = session.get("lang", "en")
        result = validate_walkthrough(fingers, required, lang=lang)
        return jsonify(result)

    @app.route("/api/game/grade", methods=["POST"])
    def game_grade():
        data = request.get_json(silent=True) or {}
        scenario = data.get("scenario", {})
        user_answer = data.get("answer", {})
        level = int(scenario.get("level", 1))
        result = grade_subnet_answer(scenario, user_answer)

        state = {
            "score": session.get("score", 0),
            "streak": session.get("streak", 0),
            "badges": session.get("badges", []),
            "levels_completed": session.get("levels_completed", {}),
        }
        state = update_score(state, level, result["correct"])
        session["score"] = state["score"]
        session["streak"] = state["streak"]
        session["badges"] = state["badges"]
        session["levels_completed"] = state["levels_completed"]
        session["game_seed"] = random.randint(1, 99999)

        lang = session.get("lang", "en")
        result["score"] = state["score"]
        result["streak"] = state["streak"]
        result["badges"] = badge_labels(state["badges"], lang)
        result["message"] = translate("correct" if result["correct"] else "incorrect", lang)
        return jsonify(result)

    @app.route("/api/game/hint", methods=["POST"])
    def game_hint():
        data = request.get_json(silent=True) or {}
        scenario = data.get("scenario", {})
        lang = session.get("lang", "en")
        question = (
            f"Give a hint for subnetting {scenario.get('network')} "
            f"requirement {scenario.get('requirement')} value {scenario.get('required_value')} "
            f"without revealing the full answer."
        )
        use_llm = bool(data.get("use_llm", False))
        context = retrieve(question, language=lang)
        result = ask_tutor(question, context, language=lang, use_llm=use_llm)
        return jsonify(result)

    @app.route("/api/finger-table")
    def finger_table_api():
        return jsonify(load_finger_table())

    return app


def main():
    build_index()
    app = create_app()
    host = os.environ.get("SUBNET_TUTOR_HOST", "127.0.0.1")
    port = int(os.environ.get("SUBNET_TUTOR_PORT", "8765"))
    print(f"Subnet Tutor running at http://{host}:{port}")
    if is_model_available():
        print("Model file found — preloading in background...")
        start_model_preload()
    else:
        print("Model not found — tutor will use RAG fallback mode")
    print(f"Model loaded: {is_model_loaded()}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
