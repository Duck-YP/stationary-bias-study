"""Compare a saved-data panel replay; never refit or reanalyze experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
PANELS = ["hist_matched_H2", "hist_matched_H4", "hist_fixed_gamma_coord1",
          "hist_fixed_gamma_coord2", "real_R0_allocation", "hist_H4_smallstep",
          "hist_H4_loglog_residual"]
E4_PANELS = ["e4_averaging_scaffold", "e4_averaging_fedavg"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_image(path):
    with pdfium.PdfDocument(path) as document:
        page = document[0]
        bitmap = page.render(scale=3)
        image = bitmap.to_pil().copy()
        bitmap.close()
        page.close()
        return image


def font_names(page):
    return {str(key): re.sub(r"^[A-Z]{6}\+", "", str(value.get_object().get("/BaseFont", "")).lstrip("/"))
            for key, value in page["/Resources"]["/Font"].items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--group", choices=("historical", "e4", "all"), default="historical",
                        help="Seven controlled/real-data panels, two E4 panels, or all nine")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/figure_audit/RELEASE_REPLAY.json")
    args = parser.parse_args()
    expected = ROOT / "manuscript/figures/redrawn"
    comparisons = []
    selected = PANELS if args.group == "historical" else (E4_PANELS if args.group == "e4" else PANELS + E4_PANELS)
    for panel in selected:
        result = {"panel_id": panel}
        for extension in ("pdf", "png"):
            name = f"{panel}.{extension}"
            result[f"{extension}_byte_identical"] = sha(expected / name) == sha(args.replay / name)
            result[f"{extension}_sha256"] = sha(expected / name)
        name = f"{panel}.csv"
        result["sidecar_byte_identical"] = sha(expected / "data" / name) == sha(args.replay / "data" / name)
        result["sidecar_sha256"] = sha(expected / "data" / name)
        geometry = expected / "data" / f"{panel}_geometry.json"
        if geometry.exists():
            replay_geometry = args.replay / "data" / geometry.name
            result["geometry_byte_identical"] = replay_geometry.is_file() and sha(geometry) == sha(replay_geometry)
        with Image.open(expected / f"{panel}.png") as left, Image.open(args.replay / f"{panel}.png") as right:
            result["raster_size"] = list(left.size)
            result["raster_pixels_identical"] = left.size == right.size and ImageChops.difference(left.convert("RGB"), right.convert("RGB")).getbbox() is None
        left_pdf = PdfReader(expected / f"{panel}.pdf")
        right_pdf = PdfReader(args.replay / f"{panel}.pdf")
        assert len(left_pdf.pages) == len(right_pdf.pages) == 1
        result["pdf_content_operators_identical"] = left_pdf.pages[0].get_contents().get_data() == right_pdf.pages[0].get_contents().get_data()
        result["pdf_font_names_equal_ignoring_subset_prefix"] = font_names(left_pdf.pages[0]) == font_names(right_pdf.pages[0])
        result["pdf_media_box_identical"] = list(left_pdf.pages[0].mediabox) == list(right_pdf.pages[0].mediabox)
        left_render = pdf_image(expected / f"{panel}.pdf")
        right_render = pdf_image(args.replay / f"{panel}.pdf")
        result["pdf_raster_pixels_identical_216dpi"] = left_render.size == right_render.size and ImageChops.difference(left_render.convert("RGB"), right_render.convert("RGB")).getbbox() is None
        comparisons.append(result)
    provenance_files = (["provenance.json"] if args.group == "historical" else
                        (["e4_provenance.json"] if args.group == "e4" else ["provenance.json", "e4_provenance.json"]))
    provenance = []
    for name in provenance_files:
        left = json.loads((expected / "data" / name).read_text(encoding="utf-8"))
        right = json.loads((args.replay / "data" / name).read_text(encoding="utf-8"))
        # E4 records a Path string: normalize only platform-specific separators.
        if name == "e4_provenance.json":
            for rows in (left, right):
                for row in rows:
                    row["source"] = row["source"].replace("\\", "/")
        provenance.append(dict(file=name, equivalent=left == right,
                               byte_identical=sha(expected / "data" / name) == sha(args.replay / "data" / name)))
    provenance_equal = all(item["equivalent"] for item in provenance)
    required = ("png_byte_identical", "sidecar_byte_identical", "raster_pixels_identical",
                "pdf_content_operators_identical", "pdf_font_names_equal_ignoring_subset_prefix",
                "pdf_media_box_identical", "pdf_raster_pixels_identical_216dpi")
    passed = provenance_equal and all(all(row[key] for key in required)
                                      and row.get("geometry_byte_identical", True) for row in comparisons)
    all_pdf_bytes = all(row["pdf_byte_identical"] for row in comparisons)
    status = "PASS" if passed and all_pdf_bytes else ("PASS_RENDER_EQUIVALENT" if passed else "MISMATCH")
    report = dict(status=status, group=args.group, panels=len(comparisons), all_pdf_bytes_identical=all_pdf_bytes,
                  pdf_byte_mismatches=sum(not row["pdf_byte_identical"] for row in comparisons),
                  canonical_provenance_identical=provenance_equal, provenance=provenance, comparisons=comparisons,
                  method="Isolated saved-record render, exact bytes and PNG pixels; no experimental recomputation",
                  no_simulation=True, no_refit=True, no_resampling=True,
                  scope="CSV, available geometry records and PNG bytes are exact; provenance is equal after normalizing E4 source path separators. All PDF operator streams, media boxes, normalized font names and 216-dpi pixels match. PDF byte identity is reported separately.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "comparisons"}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
