"""CLI helper to build the RAG index."""

from app.rag.retriever import build_index


def main() -> None:
    count = build_index(force=True)
    print(f"Indexed {count} document chunks.")


if __name__ == "__main__":
    main()
