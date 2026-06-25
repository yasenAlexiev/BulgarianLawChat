"""
Batch corpus build: data/raw/*.txt -> processed -> normalized -> chunks.

Usage:
  python -m app.integration.corpus_pipeline
  python -m app.integration.corpus_pipeline --ingest
  python -m app.integration.corpus_pipeline data/raw/кодекс-на-труда.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.integration.normalizer import normalize_file
from app.integration.parser import parse_law_text
from app.rag.chunker import chunk_file

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
NORMALIZED_DIR = DATA_DIR / "normalized"
CHUNKS_DIR = DATA_DIR / "chunks"


def process_txt(
    input_path: Path,
    *,
    processed_dir: Path = PROCESSED_DIR,
    normalized_dir: Path = NORMALIZED_DIR,
    chunks_dir: Path = CHUNKS_DIR,
) -> tuple[Path, Path, Path]:
    stem = input_path.stem
    processed_path = processed_dir / f"{stem}.json"
    normalized_path = normalized_dir / f"{stem}.json"
    chunks_path = chunks_dir / f"{stem}.json"

    parsed = parse_law_text(input_path.read_text(encoding="utf-8"))
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    normalize_file(processed_path, normalized_path)
    chunk_file(normalized_path, chunks_path)

    return processed_path, normalized_path, chunks_path


def process_all(
    raw_dir: Path = RAW_DIR,
    *,
    ingest: bool = False,
) -> int:
    txt_files = sorted(raw_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {raw_dir}")

    for txt_path in txt_files:
        processed_path, normalized_path, chunks_path = process_txt(txt_path)
        print(f"{txt_path.name}")
        print(f"  -> {processed_path}")
        print(f"  -> {normalized_path}")
        print(f"  -> {chunks_path}")

    if ingest:
        from app.db.session import init_db
        from app.rag.embeddings import reset_embedder
        from app.rag.ingest import ingest_path

        init_db()
        reset_embedder()
        count = ingest_path(CHUNKS_DIR)
        print(f"Ingested {count} chunks into PostgreSQL.")

    return len(txt_files)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the law corpus from raw .txt files through "
            "processed, normalized, and chunks JSON stages."
        )
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific .txt files to process (default: all files in data/raw/)",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="After chunking, embed and upsert all chunks into PostgreSQL",
    )
    args = parser.parse_args(argv)

    if args.files:
        for file_arg in args.files:
            input_path = Path(file_arg)
            if not input_path.is_file():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            processed_path, normalized_path, chunks_path = process_txt(input_path)
            print(f"{input_path.name}")
            print(f"  -> {processed_path}")
            print(f"  -> {normalized_path}")
            print(f"  -> {chunks_path}")

        if args.ingest:
            from app.db.session import init_db
            from app.rag.embeddings import reset_embedder
            from app.rag.ingest import ingest_path

            init_db()
            reset_embedder()
            count = ingest_path(CHUNKS_DIR)
            print(f"Ingested {count} chunks into PostgreSQL.")
        return

    count = process_all(ingest=args.ingest)
    print(f"Done. Processed {count} law file(s).")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
