"""Audit real final PDF glyph sizes, including rotated labels and XObjects."""
import argparse
import json
import math
from pathlib import Path

from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import mult_matrix
from pypdf import PdfReader
from pypdf.generic import ContentStream

from figures import PANELS
from prepare import write_csv


class GlyphDevice(PDFPageAggregator):
    def __init__(self, manager):
        super().__init__(manager)
        self.glyphs = []

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        adv = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        item = self.cur_item._objs[-1]
        self.glyphs.append(dict(text=item.get_text(), font=str(font.fontname), bbox=list(item.bbox),
                               pt=float(fontsize)*min(math.hypot(*matrix[:2]), math.hypot(*matrix[2:4]))))
        return adv


def glyphs(path):
    result = []
    with Path(path).open('rb') as f:
        manager = PDFResourceManager()
        device = GlyphDevice(manager)
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(f):
            device.glyphs = []
            interpreter.process_page(page)
            result.append([g for g in device.glyphs if g['text'].strip()])
    return result


def audit(root):
    root = Path(root)
    doc = PdfReader(root / 'E4_FIGURES_GALLERY.pdf')
    final = glyphs(root / 'E4_FIGURES_GALLERY.pdf')
    placements = []
    def walk(stream, resources, matrix, page):
        stack = []
        for args, op in ContentStream(stream, doc).operations:
            if op == b'q':
                stack.append(matrix)
            elif op == b'Q':
                matrix = stack.pop()
            elif op == b'cm':
                matrix = mult_matrix(tuple(map(float, args)), matrix)
            elif op == b'Do':
                obj = resources['/XObject'][args[0]].get_object()
                if obj.get('/Subtype') != '/Form':
                    continue
                name = Path(str(obj.get('/PTEX.FileName', '')).replace('\\', '/')).stem
                inner = mult_matrix(tuple(map(float, obj.get('/Matrix', [1, 0, 0, 1, 0, 0]))), matrix)
                if name in PANELS:
                    placements.append((page, name, inner, list(map(float, obj['/BBox']))))
                else:
                    walk(obj, obj.get('/Resources', resources), inner, page)
    for pi, page in enumerate(doc.pages):
        walk(page.get_contents(), page['/Resources'], (1, 0, 0, 1, 0, 0), pi)
    assert len(placements) == 4 and {p[1] for p in placements} == set(PANELS)
    rows = []
    for pi, name, m, box in placements:
        a, b, c, d, e, f = m
        corners = [(a*x+c*y+e, b*x+d*y+f) for x in [box[0], box[2]] for y in [box[1], box[3]]]
        bounds = [min(x for x, y in corners), min(y for x, y in corners), max(x for x, y in corners), max(y for x, y in corners)]
        gg = [g for g in final[pi] if bounds[0]-.2 <= (g['bbox'][0]+g['bbox'][2])/2 <= bounds[2]+.2 and
              bounds[1]-.2 <= (g['bbox'][1]+g['bbox'][3])/2 <= bounds[3]+.2]
        path = root / 'figures' / (name+'.pdf')
        src = PdfReader(path)
        sg = glyphs(path)[0]
        assert len(gg) == len(sg), (name, len(gg), len(sg))
        minimum = min(g['pt'] for g in gg)*72.27/72
        assert minimum >= 9, (name, minimum)
        assert not list(src.pages[0].images), 'Raster figure found'
        fonts = []
        for font in src.pages[0]['/Resources']['/Font'].values():
            font = font.get_object()
            desc = font['/FontDescriptor'].get_object()
            assert any(k in desc for k in ['/FontFile', '/FontFile2', '/FontFile3'])
            fonts.append(str(font['/BaseFont']))
        bb = list(map(float, src.pages[0].mediabox))
        clipped = [g for g in sg if g['bbox'][0] < -.25 or g['bbox'][1] < -.25 or g['bbox'][2] > bb[2]+.25 or g['bbox'][3] > bb[3]+.25]
        assert not clipped, (name, clipped)
        rows.append(dict(panel=name, page=pi+1, glyph_count=len(gg), minimum_final_TeX_pt=minimum,
                         inserted_width_PDF_pt=bounds[2]-bounds[0], fonts=';'.join(fonts),
                         vector=True, all_fonts_embedded=True, clipped_text=0, status='PASS'))
    write_csv(root / 'FINAL_FONT_AUDIT.csv', rows)
    (root / 'FINAL_FONT_AUDIT.md').write_text('# Final Font Audit\n\nPASS: four independent vector panels in the compiled LaTeX gallery.\n\n'
        f"Smallest actual final glyph: {min(r['minimum_final_TeX_pt'] for r in rows):.8f} TeX pt; required floor9pt.\n\n"
        'Audited glyph text matrices including rotated y labels and Form XObject placement. All fonts embedded; no raster images or clipped source text. Visual page QA is separately recorded.\n')
    print(json.dumps(rows))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    audit(p.parse_args().root)
