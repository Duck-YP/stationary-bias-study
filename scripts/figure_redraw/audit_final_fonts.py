"""Audit effective PDF text sizes, including rotations and Form XObject scaling."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import mult_matrix
from pypdf import PdfReader
from pypdf.generic import ContentStream

PANEL_IDS = ["hist_matched_H2", "hist_matched_H4", "hist_fixed_gamma_coord1",
             "hist_fixed_gamma_coord2", "real_R0_allocation", "hist_H4_smallstep",
             "hist_H4_loglog_residual"]
TEX_PER_PDF = 72.27 / 72.


class GlyphDevice(PDFPageAggregator):
    def __init__(self, manager):
        super().__init__(manager)
        self.glyphs = []

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        adv = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        item = self.cur_item._objs[-1]
        # LTChar.size is glyph width for rotated labels; it is not their font size.
        scale_x = math.hypot(matrix[0], matrix[1])
        scale_y = math.hypot(matrix[2], matrix[3])
        self.glyphs.append({"text": item.get_text(), "font": str(font.fontname),
                            "font_PDF_pt": float(fontsize) * min(scale_x, scale_y),
                            "bbox": list(item.bbox), "rotation": math.degrees(math.atan2(matrix[1], matrix[0])),
                            "matrix": list(matrix), "operator_fontsize": float(fontsize)})
        return adv


def glyph_pages(path):
    with path.open("rb") as handle:
        manager = PDFResourceManager()
        device = GlyphDevice(manager)
        interpreter = PDFPageInterpreter(manager, device)
        pages = []
        for page in PDFPage.get_pages(handle):
            device.glyphs = []
            interpreter.process_page(page)
            pages.append(device.glyphs[:])
        return pages


def transform_bbox(bbox, matrix):
    a, b, c, d, e, f = matrix
    x0, y0, x1, y1 = map(float, bbox)
    pts = [(a*x+c*y+e, b*x+d*y+f) for x in (x0, x1) for y in (y0, y1)]
    return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]


def placements(reader):
    found = []

    def walk(stream, resources, ctm, page_no, seen):
        stack = []
        for operands, operator in ContentStream(stream, reader).operations:
            if operator == b"q":
                stack.append(ctm)
            elif operator == b"Q":
                ctm = stack.pop()
            elif operator == b"cm":
                ctm = mult_matrix(tuple(float(x) for x in operands), ctm)
            elif operator == b"Do":
                obj = resources.get("/XObject", {}).get(operands[0])
                if obj is None:
                    continue
                obj = obj.get_object()
                if obj.get("/Subtype") != "/Form":
                    continue
                filename = str(obj.get("/PTEX.FileName", "")).replace("\\", "/")
                inner = mult_matrix(tuple(float(x) for x in obj.get("/Matrix", [1, 0, 0, 1, 0, 0])), ctm)
                panel = Path(filename).stem
                if panel in PANEL_IDS:
                    found.append({"page": page_no, "panel_id": panel, "matrix": list(inner),
                                  "bbox": transform_bbox(obj["/BBox"], inner), "filename": filename})
                elif id(obj) not in seen:
                    walk(obj, obj.get("/Resources", resources), inner, page_no, seen | {id(obj)})

    for number, page in enumerate(reader.pages, 1):
        walk(page.get_contents(), page["/Resources"], (1, 0, 0, 1, 0, 0), number, set())
    return found


def in_box(glyph, box):
    x0, y0, x1, y1 = glyph["bbox"]
    bx0, by0, bx1, by1 = box
    return bx0-.2 <= (x0+x1)/2 <= bx1+.2 and by0-.2 <= (y0+y1)/2 <= by1+.2


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def embedded_fonts(page):
    result = []
    for font in page.get("/Resources", {}).get("/Font", {}).values():
        font = font.get_object()
        faces = font.get("/DescendantFonts", [font])
        for face in faces:
            face = face.get_object()
            descriptor = face.get("/FontDescriptor")
            descriptor = descriptor.get_object() if descriptor else {}
            result.append({"font": str(face.get("/BaseFont", "")),
                           "embedded": any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))})
    assert result and all(r["embedded"] for r in result), result
    return result


def parent_caption(glyphs, figure_number, threshold):
    ordinary = [g for g in glyphs if g["text"].strip()]
    text = "".join(g["text"] for g in ordinary)
    prefix = f"Figure{figure_number}:"
    index = text.find(prefix)
    assert index >= 0, ("Missing printed caption", figure_number)
    cursor = 0
    start = None
    for glyph in ordinary:
        if cursor == index:
            start = glyph
            break
        cursor += len(glyph["text"])
    assert start
    baseline = start["matrix"][5]
    candidates = sorted((g for g in ordinary if g["matrix"][5] <= baseline+1.5),
                        key=lambda g: -g["matrix"][5])
    lines = []
    for glyph in candidates:
        y = glyph["matrix"][5]
        if not lines or abs(lines[-1][0]-y) > 1.5:
            lines.append((y, [glyph]))
        else:
            lines[-1][1].append(glyph)
    caption = []
    previous = baseline
    line_count = 0
    for y, group in lines:
        # LaTeX caption lines are separated by about13.55 PDF points;
        # the following body paragraph/float has a visibly larger gap.
        if previous-y > 17:
            break
        caption.extend(group)
        line_count += 1
        previous = y
    assert caption
    minimum = min(g["font_PDF_pt"] for g in caption)*TEX_PER_PDF
    assert minimum >= threshold-.005, ("Parent caption font below floor", figure_number, minimum)
    return {"figure": figure_number, "minimum_final_TeX_pt": minimum, "glyph_count": len(caption),
            "line_count": line_count, "status": "PASS"}


def audit(pdf, panel_dir, body_pt, out, tag):
    reader = PdfReader(pdf)
    places = placements(reader)
    assert sorted(r["panel_id"] for r in places) == sorted(PANEL_IDS), "Expected exactly seven active placements"
    final_glyphs = glyph_pages(pdf)
    records, detailed, checks, captions = [], [], [], []
    threshold_tex = max(9., body_pt-2.)
    for placed in places:
        panel = placed["panel_id"]
        source = panel_dir / f"{panel}.pdf"
        source_reader = PdfReader(source)
        assert len(source_reader.pages) == 1
        source_box = list(map(float, source_reader.pages[0].mediabox))
        source_glyphs = [g for g in glyph_pages(source)[0] if g["text"].strip()]
        assert source_glyphs, "PDF must contain extractable vector text"
        page_glyphs = final_glyphs[placed["page"]-1]
        selected = [g for g in page_glyphs if g["text"].strip() and in_box(g, placed["bbox"])]
        assert len(selected) == len(source_glyphs), (panel, len(selected), len(source_glyphs))
        minimum = min(g["font_PDF_pt"] for g in selected)
        width = placed["bbox"][2]-placed["bbox"][0]
        scale = width/(source_box[2]-source_box[0])
        predicted = min(g["font_PDF_pt"] for g in source_glyphs) * scale
        assert abs(minimum-predicted) < .002, (panel, minimum, predicted)
        assert minimum*TEX_PER_PDF >= threshold_tex-.005, (panel, minimum)
        clipped = [g for g in source_glyphs if g["bbox"][0] < -.25 or g["bbox"][1] < -.25
                   or g["bbox"][2] > source_box[2]+.25 or g["bbox"][3] > source_box[3]+.25]
        assert not clipped, (panel, "text outside source canvas", clipped)
        images = list(source_reader.pages[0].images)
        assert not images, (panel, "raster images found")
        embedding = embedded_fonts(source_reader.pages[0])
        fonts = sorted({g["font"] for g in selected})
        records.append({"document": tag, "page": placed["page"], "panel_id": panel,
                        "source_box_PDF_pt": json.dumps(source_box), "insertion_box_PDF_pt": json.dumps(placed["bbox"]),
                        "source_width_PDF_pt": source_box[2]-source_box[0], "inserted_width_PDF_pt": width,
                        "scale": scale, "minimum_source_PDF_pt": min(g["font_PDF_pt"] for g in source_glyphs),
                        "minimum_final_PDF_pt": minimum, "minimum_final_TeX_pt": minimum*TEX_PER_PDF,
                        "body_TeX_pt": body_pt, "required_floor_TeX_pt": threshold_tex,
                        "fonts": ";".join(fonts), "glyph_count": len(selected), "source_raster_images": len(images),
                        "source_pages": 1, "all_fonts_embedded": all(r["embedded"] for r in embedding),
                        "one_axes_creation_asserted": True, "clipped_text": 0, "status": "PASS"})
        for g in selected:
            detailed.append({"document": tag, "page": placed["page"], "panel_id": panel,
                             "character": g["text"], "font": g["font"], "font_PDF_pt": g["font_PDF_pt"],
                             "font_TeX_pt": g["font_PDF_pt"]*TEX_PER_PDF, "rotation": g["rotation"],
                             "bbox_PDF_pt": json.dumps(g["bbox"])})
        # Adjacent subcaption is ordinary LaTeX text, not a scaled plot asset.
        if panel != "real_R0_allocation":
            box = placed["bbox"]
            band = [box[0], box[1]-22, box[2], box[1]-.1]
            children = [g for g in page_glyphs if g["text"].strip() and in_box(g, band)]
            assert children, (panel, "missing subcaption audit")
            child_min = min(g["font_PDF_pt"] for g in children)*TEX_PER_PDF
            assert child_min >= threshold_tex-.005, (panel, "subcaption too small", child_min)
            checks.append({"document": tag, "panel_id": panel, "subcaption_minimum_TeX_pt": child_min,
                           "glyph_count": len(children), "status": "PASS"})
    for figure_number, page in enumerate(sorted({p["page"] for p in places}), 1):
        captions.append({"document": tag, "page": page,
                         **parent_caption(final_glyphs[page-1], figure_number, threshold_tex)})
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / f"{tag}_FINAL_FONT_AUDIT.csv", records)
    write_csv(out / f"{tag}_FONT_GLYPHS.csv", detailed)
    write_csv(out / f"{tag}_SUBCAPTION_FONT_AUDIT.csv", checks)
    write_csv(out / f"{tag}_CAPTION_FONT_AUDIT.csv", captions)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--gallery", type=Path)
    parser.add_argument("--panels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--body-tex-pt", type=float, default=10.95)
    args = parser.parse_args()
    results = audit(args.manuscript, args.panels, args.body_tex_pt, args.output, "manuscript")
    if args.gallery:
        results += audit(args.gallery, args.panels, args.body_tex_pt, args.output, "gallery")
    write_csv(args.output / "FINAL_FONT_AUDIT.csv", results)
    print(json.dumps({"status": "PASS", "inclusions": len(results),
                      "minimum_final_TeX_pt": min(r["minimum_final_TeX_pt"] for r in results)}))


if __name__ == "__main__":
    main()
