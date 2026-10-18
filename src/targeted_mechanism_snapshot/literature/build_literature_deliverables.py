"""Generate review-only literature snippets, diff and evidence manifest.

Run from repository root. Writes only beneath targeted_closure_20261014/literature.
No manuscript mutation or network request is performed by this script.
"""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
rw_path = ROOT / "manuscript/sections/02_related_work.tex"
bib_path = ROOT / "manuscript/references.bib"

glasgow = r"""Stochastic local updates can introduce bias even without objective
heterogeneity. \citet{glasgow2022sharp} study \emph{iterate bias}, the
deviation of the expected SGD trajectory from deterministic gradient
descent with the same initialization, and obtain sharp finite-step bounds
under second- and third-order smoothness. Their infinite-client round-map
viewpoint and continuous analysis already connect local stochastic bias
to nonlinearity and noise. Our estimand is the invariant-law global mean
relative to the minimizer. Building on these mechanisms, our analysis
resolves matched stationary coefficients and their joint small-step,
large-client remainder.

"""

controls = r"""The leading stationary covariance of the persistent controls is also
already explicit in \citet[Lemma~5.1]{mangold2025scaffold}; on the shared
submodel it equals $(1-1/N)C/H+O_H(\gamma)$. Its contribution to
within-round second moments provides a direct precursor to the additional
coefficient isolated here. The claimed refinement is the explicit
matched stationary increment together with the $N$-uniform remainder,
which requires resolving terms absorbed into the earlier error bounds.

"""

old_rw = rw_path.read_text(encoding="utf-8")
old_bib = bib_path.read_text(encoding="utf-8")
if "glasgow2022sharp" in old_bib:
    raise RuntimeError("Glasgow key already exists: reconcile the current baseline explicitly")
anchor = "Beyond finite-time convergence, constant-step stochastic optimization"
anchor2 = "The controlled experiments in Section~\\ref{sec:num-controlled}"
assert old_rw.count(anchor) == old_rw.count(anchor2) == 1
new_rw = old_rw.replace(anchor, glasgow + anchor).replace(anchor2, controls + anchor2)
brief = ROOT / "targeted_closure_20261014/brief/SCAFFOLD_Targeted_Closure_20261014"
bib = (brief / "glasgow2022sharp.bib").read_text(encoding="utf-8")
new_bib = old_bib.rstrip() + "\n\n" + bib.rstrip() + "\n"
(OUT / "proposed_related_work_insert.tex").write_text(glasgow + "% Additional insertion before the controlled-experiments paragraph.\n" + controls, encoding="utf-8")
(OUT / "proposed_glasgow2022sharp.bib").write_text(bib, encoding="utf-8")
patch = "".join(difflib.unified_diff(old_rw.splitlines(True), new_rw.splitlines(True),
    fromfile="a/manuscript/sections/02_related_work.tex", tofile="b/manuscript/sections/02_related_work.tex"))
patch += "".join(difflib.unified_diff(old_bib.splitlines(True), new_bib.splitlines(True),
    fromfile="a/manuscript/references.bib", tofile="b/manuscript/references.bib"))
(OUT / "proposed_related_work.patch").write_text(patch, encoding="utf-8")

sources = [
    {"id":"glasgow_pmlr", "file":"glasgow2022_pmlr.pdf", "url":"https://proceedings.mlr.press/v151/glasgow22a/glasgow22a.pdf", "version":"PMLR 151 (2022)", "anchors":{"Definition 2.1":[5],"Assumptions 1-2":[5,6],"Theorems 2.4-2.5; Section 2.3":[6,7],"Theorems A.3-A.4":[14]}, "visual_qa":["qa_glasgow-06.png"]},
    {"id":"fedavg_v2", "file":"mangold_fedavg_v2.pdf", "url":"https://arxiv.org/pdf/2412.01389v2", "version":"arXiv:2412.01389v2", "anchors":{"A1":[3],"A3":[5],"A6; Theorems 3-4":[7],"Appendix B.5-B.6":list(range(33,43))}},
    {"id":"fedavg_pmlr", "file":"mangold_fedavg_pmlr.pdf", "url":"https://raw.githubusercontent.com/mlresearch/v258/main/assets/mangold25a/mangold25a.pdf", "version":"Official PMLR 258 (2025), landing https://proceedings.mlr.press/v258/mangold25a.html", "purpose":"Compared the stationary mean formulas/remainders with the manuscript-cited v2"},
    {"id":"scaffold_v1", "file":"mangold_scaffold_v1.pdf", "url":"https://arxiv.org/pdf/2503.07594v1", "version":"arXiv:2503.07594v1", "anchors":{"A1-A5":[2,3],"A6; Theorem 5.3":[8],"Lemma 5.1":[7,42],"Lemma E.3":[43,44],"Lemma E.4":[44],"Theorem 5.3 restated":[45]}, "visual_qa":["qa_scaffold-42.png","qa_scaffold_detail-44.png"]},
    {"id":"scaffold_pmlr", "file":"mangold_scaffold_pmlr.pdf", "url":"https://raw.githubusercontent.com/mlresearch/v267/main/assets/mangold25a/mangold25a.pdf", "version":"Official PMLR 267 (2025), landing https://proceedings.mlr.press/v267/mangold25a.html", "purpose":"Compared the stationary mean formula/remainder with the manuscript-cited v1"},
    {"id":"ddb_v2", "file":"dieuleveut_arxiv_v2.pdf", "url":"https://arxiv.org/pdf/1707.06386v2", "version":"arXiv v2, dated April 12, 2018; not claimed identical to final 2020 journal article", "anchors":{"A1-A5":[5,6],"Theorem 4":[13,14],"Theorem 7":[17]}, "visual_qa":["qa_ddb-13.png"]},
    {"id":"ddb_earlier_author", "file":"dieuleveut_author_20180326.pdf", "url":"https://www.cmap.polytechnique.fr/~aymeric.dieuleveut/papers/Dieuleveut-Durmus-Bach.pdf", "version":"Author-hosted manuscript; footer March 26, 2018", "anchors":{"Theorem 4":[13]}, "purpose":"Cross-checked the coefficient as printed in another primary author version"},
]
for s in sources:
    p=OUT/"sources"/s["file"]
    s.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size,
             access="downloaded primary PDF; relevant full pages read using pdftotext -layout", page_numbering="one-based PDF pages")

baseline=[]
for rel in ["main.tex","sections/02_related_work.tex","sections/03_setting_preliminaries.tex","sections/04_main_results.tex","references.bib"]:
    p=ROOT/"manuscript"/rel
    baseline.append({"path":"manuscript/"+rel,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})

manifest={
    "audit_date_local":"2026-10-14", "timezone":"Asia/Taipei", "scope":{"required_papers":4,"additional_papers":0},
    "baseline_files":baseline,"sources":sources,
    "access_gaps":[{"url":"https://doi.org/10.1214/19-AOS1850", "status":"web tool inaccessible"},{"url":"https://projecteuclid.org/journals/annals-of-statistics/volume-48/issue-3/Bridging-the-gap-between-constant-step-size-stochastic-gradient-descent/10.1214/19-AOS1850.full", "status":"wrapper only, final publisher article not read"}],
    "network_note":"Initial sandbox HTTP downloads could not resolve hosts. Approved read-only primary-source downloads then succeeded. No paywall bypass used.",
    "packaging":"Keep PDFs, extracted full texts and QA renders under literature/sources locally. Distribute report, proposed patch/snippets and this manifest; source retrieval URLs and hashes suffice for a compact review bundle.",
    "no_master_mutation":True,"patch_is_unapplied":True,
}
(OUT/"SOURCE_EVIDENCE.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"output_directory":str(OUT),"source_pdfs":len(sources),"patch_bytes":len(patch.encode()),"baseline_sha256":baseline},indent=2))
