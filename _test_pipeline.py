from pathlib import Path

from app.integration.normalizer import normalize_file
from app.rag.chunker import chunk_file

root = Path(__file__).resolve().parent
processed = root / "data" / "processed" / "закон-за-административни-надушения-и-наказания.json"
normalized = root / "data" / "normalized" / processed.name
chunks = root / "data" / "chunks" / processed.name

docs = normalize_file(processed, normalized)
print("documents:", len(docs))

chs = chunk_file(normalized, chunks)
print("chunks:", len(chs))

chl28 = [c for c in chs if c.article == "чл. 28"]
print("chl28 chunks:", len(chl28))
for c in chl28[:3]:
    print(c.chunk_id, c.paragraph, c.text[:120])
