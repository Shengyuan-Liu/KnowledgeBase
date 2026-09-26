"""Exercise the complete adapter with local models and original PDF bytes."""

import json
from pathlib import Path
import resource
import sys
import time

from knowledgebase.rag.pdf import PdfParser

DIRECTORY = Path(__file__).parent

if __name__ == "__main__":
    target = DIRECTORY / sys.argv[1]
    target.mkdir(exist_ok=False)
    start = time.perf_counter()
    parser = PdfParser(Path(sys.argv[2]))
    setup_seconds = time.perf_counter() - start
    records = []
    manifest = json.loads(Path("evals/materials/pdf-v2/manifest.json").read_text())
    page_counts = {entry["file"]: entry["pages"] for entry in manifest}
    for name in ["apple-fy24", "docling-report"]:
        start = time.perf_counter()
        result = parser.parse(Path(f"evals/materials/pdf-v2/{name}.pdf").read_bytes())
        seconds = time.perf_counter() - start
        (target / f"{name}.json").write_text(result.model_dump_json(indent=2) + "\n")
        assert result.page_count == page_counts[f"{name}.pdf"]
        for block in result.blocks:
            assert block.text == result.text[block.start_offset:block.end_offset]
            assert all(block.start_offset <= r.start_offset <= r.end_offset <= block.end_offset
                       for r in block.regions)
        assert any(b.table for b in result.blocks)
        records.append({"file": name, "seconds": seconds, "pages": result.page_count,
                        "blocks": len(result.blocks), "warnings": len(result.warnings),
                        "regions": sum(len(b.regions) for b in result.blocks), "status": "success"})
        (target / "timings.json").write_text(json.dumps({
            "setup_seconds_including_model_hashing": setup_seconds,
            "first_parse_includes_model_loading": True, "concurrency": 1,
            "cases": records, "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }, indent=2) + "\n")
        print(f"{name}: {result.page_count} pages; {seconds:.3f}s; exact-slice checks passed.", flush=True)
