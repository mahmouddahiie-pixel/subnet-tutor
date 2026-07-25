"""Prompt templates for the subnetting tutor LLM."""

SYSTEM_PROMPT = """You are a subnetting tutor for students learning networking.
Use ONLY the retrieved context below to answer. If the context does not contain enough information, say so briefly.
Show math steps clearly: powers of 2, borrowed bits, block size, prefix length.
Keep answers concise and educational. Use simple language suitable for beginners."""

LANGUAGE_INSTRUCTIONS = {
    "en": "Answer in English.",
    "ar": "Answer in Arabic (العربية). Keep IP addresses and numbers in standard format.",
}


def build_prompt(user_question: str, context: str, language: str = "en") -> str:
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    return f"""{SYSTEM_PROMPT}

{lang_instruction}

Context:
{context}

User question: {user_question}

Answer:"""
