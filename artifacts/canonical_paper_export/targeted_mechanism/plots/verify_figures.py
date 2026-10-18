"""Verify final PDFs and source hashes; render all panels for visual review.

Requires Poppler's pdftoppm, pdftotext, pdfimages and pdffonts on PATH.
Writes only beneath this plots directory. Does not modify figures or CSVs.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent


def call(*args):
    return subprocess.run(args,check=True,capture_output=True,encoding="utf-8",errors="replace").stdout


def main():
    manifest=json.loads((HERE/"FIGURE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["mock"] is False and manifest["panel_count"]==32
    current={name:hashlib.sha256((STUDY/"results"/name).read_bytes()).hexdigest() for name in manifest["input_sha256"]}
    assert current==manifest["input_sha256"], "Input CSV hashes changed after figure generation"
    assert hashlib.sha256((STUDY/"PROTOCOL_FROZEN.json").read_bytes()).hexdigest()==manifest["protocol_sha256"]
    assert hashlib.sha256((HERE/"plot_mechanism_checks.py").read_bytes()).hexdigest()==manifest["script_sha256"]
    qa=HERE/"scratch/final_pdf_qa"
    qa.mkdir(parents=True,exist_ok=True)
    results=[]
    for row in manifest["panels"]:
        pdf=HERE/row["file"]
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==row["sha256"]
        xml=ET.fromstring(call("pdftotext","-bbox","-enc","UTF-8",str(pdf),"-"))
        pages=xml.findall(".//{*}page")
        assert len(pages)==1
        page=pages[0]; width=float(page.attrib["width"]); height=float(page.attrib["height"])
        outside=[]
        for word in page.findall(".//{*}word"):
            a=word.attrib
            if float(a["xMin"])<-.5 or float(a["yMin"])<-.5 or float(a["xMax"])>width+.5 or float(a["yMax"])>height+.5:
                outside.append(dict(word=word.text,bounds=a))
        assert not outside,(row["file"],outside)
        fonts=call("pdffonts",str(pdf)).splitlines()[2:]
        assert fonts and all("TrueType" in line and "yes yes yes" in line for line in fonts),fonts
        images=call("pdfimages","-list",str(pdf)).splitlines()[2:]
        assert not [x for x in images if x.strip()], "Unexpected raster image"
        call("pdftoppm","-f","1","-l","1","-scale-to","1000","-png",str(pdf),str(qa/pdf.stem))
        results.append(dict(file=row["file"],pages=1,text_outside_page=outside,embedded_truetype=True,
                            raster_images=0,rendered_png=str((qa/(pdf.stem+"-1.png")).relative_to(HERE))))
    report=dict(panel_count=len(results),all_input_hashes_current=True,input_sha256=current,
        all_pdf_hashes_match=True,all_single_page_vector=True,all_fonts_embedded_truetype=True,
        all_pdf_text_within_page=True,results=results,
        visual_review_note="Rendered PNGs are retained in scratch/final_pdf_qa; main panels and supplementary layout cases reviewed separately.")
    (HERE/"FIGURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))


if __name__=="__main__":
    main()
