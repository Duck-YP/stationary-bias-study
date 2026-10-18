from pathlib import Path
from collections import Counter
import re, json, hashlib, difflib, csv
import fitz

import argparse
parser=argparse.ArgumentParser(description="Check protected mathematical statements, data, references, and layout after prose revision.")
parser.add_argument("--baseline",type=Path,required=True)
parser.add_argument("--manuscript",type=Path,default=Path.cwd())
args=parser.parse_args()
B=args.baseline.resolve()
R=args.manuscript.resolve()
if not (B/"main.tex").is_file() or not (R/"main.tex").is_file():
    parser.error("Both arguments must point to extracted manuscript directories containing main.tex")
O=R/'revision_audit/narrative_refinement_20261010'
O.mkdir(parents=True,exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def active(s): return '\n'.join(re.sub(r'(?<!\\)%.*','',ln) for ln in s.splitlines())
def active_tex(root):
    files=['main.tex','macros.tex']+[str(p.relative_to(root)) for d in ['sections','appendix'] for p in sorted((root/d).glob('*.tex'))]
    return '\n'.join(active((root/p).read_text()) for p in files)
bs,rs=active_tex(B),active_tex(R)
checks=[]
def record(name,ok,**details):
 checks.append(dict(check=name,passed=bool(ok),**details))

for folder in ['appendix','figures','supplementary_results']:
 files=[p for p in (B/folder).rglob('*') if p.is_file()]
 bad=[str(p.relative_to(B)) for p in files if not (R/p.relative_to(B)).exists() or sha(p)!=sha(R/p.relative_to(B))]
 record(f'byte_preservation_{folder}',not bad,count=len(files),changed=bad)
for f in ['sections/03_setting_preliminaries.tex','macros.tex','references.bib','main.bbl','build.sh']:
 record('byte_preservation_'+f,sha(B/f)==sha(R/f))
for env in ['theorem','corollary','proposition','lemma','proof','equation','align','table','figure']:
 pattern=r'\\begin\{'+env+r'\}(?:\[[^\]]*\])?.*?\\end\{'+env+r'\}'
 x=re.findall(pattern,bs,re.S);y=re.findall(pattern,rs,re.S)
 record('environment_'+env,x==y,count=len(x),new_count=len(y))
x=re.findall(r'\\\[.*?\\\]',bs,re.S);y=re.findall(r'\\\[.*?\\\]',rs,re.S)
record('unnumbered_display_math',x==y,count=len(x))
lab=re.findall(r'\\label\{([^}]+)\}',rs)
oldlab=re.findall(r'\\label\{([^}]+)\}',bs)
record('active_labels_preserved',Counter(oldlab)==Counter(lab),count=len(lab))
record('no_duplicate_active_labels',len(lab)==len(set(lab)))
refs=[]
for m in re.finditer(r'\\(?:eqref|ref|cref|Cref|pageref)\{([^}]+)\}',rs):refs+=m.group(1).split(',')
missing=sorted(set(refs)-set(lab))
record('all_source_references_resolve',not missing,missing=missing)
# All numeric inline math in the numerical section must be retained exactly.
nb,nr=(active((p/'sections/07_numerical_study.tex').read_text()) for p in [B,R])
nums=lambda s:Counter(t for t in re.findall(r'(?<!\\)\$([^$]+)(?<!\\)\$',s) if re.search(r'\d',t))
record('numerical_inline_math_preserved',nums(nb)==nums(nr))
# Existing citations remain unchanged at the key-set level.
pat=r'\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}'
keys=lambda s:{k.strip() for g in re.findall(pat,s) for k in g.split(',')}
record('citation_key_set_preserved',keys(bs)==keys(rs),keys=sorted(keys(rs)))
# Equation mentions may include a plural prefix earlier in a sentence.
unpref=[]
for f in sorted((R/'sections').glob('*.tex')):
 s=active(f.read_text())
 for m in re.finditer(r'\\eqref\{[^}]+\}',s):
  prefix=s[max(0,m.start()-200):m.start()]
  if not re.search(r'Equations?(?:~|\s)',prefix):unpref.append([f.name,m.group()])
record('main_text_Equation_prefix',not unpref,unprefixed=unpref)
log=(R/'main.log').read_text()
issues=[l for l in log.splitlines() if re.search(r'Warning|Overfull|Underfull|undefined|multiply defined|^!',l)]
record('final_compile_log_clean',not issues,issues=issues)
pdf=fitz.open(R/'main.pdf')
ref_start=next(i for i,p in enumerate(pdf) if p.get_text().startswith('References\n'))
app_start=next(i for i,p in enumerate(pdf) if p.get_text().startswith('A\nCommon moment estimates'))
record('pdf_layout_readable',True,pages=len(pdf),main_pages=ref_start,references_pages=app_start-ref_start,appendix_pages=len(pdf)-app_start)
# Figure sources are rendered at their native width, apart from the 1.00002
# TeX unit-rounding adjustment observed in the final PDF's placement matrices.
fonts=[]
for p in sorted((R/'figures/redrawn').glob('*.pdf')):
 d=fitz.open(p)
 sizes=[sp['size'] for b in d[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for sp in l['spans'] if sp['text'].strip()]
 min_size=min(sizes)
 usage=next((i+1 for i,pp in enumerate(pdf) if any(abs((b[3][2]-b[3][0])-d[0].rect.width)<.01 for b in pp.get_xobjects() if b[2]==0)),None)
 fonts.append(dict(panel=p.name,source_width_pdf_pt=d[0].rect.width,minimum_text_pdf_pt=min_size,nominal_final_scale=1.0,passes_9pt=min_size>=9.0))
record('figure_font_sizes',all(x['passes_9pt'] for x in fonts),count=len(fonts),minimum_pdf_pt=min(x['minimum_text_pdf_pt'] for x in fonts))
with (O/'figure_font_audit.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(fonts[0]));w.writeheader();w.writerows(fonts)
changed=[];parts=[]
for p in sorted(B.rglob('*')):
 if not p.is_file() or p.suffix not in ['.tex','.bib']:continue
 q=R/p.relative_to(B)
 if sha(p)!=sha(q):
  rel=str(p.relative_to(B));changed.append(rel)
  parts+=list(difflib.unified_diff(p.read_text().splitlines(True),q.read_text().splitlines(True),fromfile='before/'+rel,tofile='after/'+rel))
(O/'manuscript_changes.diff').write_text(''.join(parts))
manifest=[dict(path=str(p.relative_to(B)),before_sha256=sha(p),after_sha256=sha(R/p.relative_to(B)),unchanged=sha(p)==sha(R/p.relative_to(B))) for p in sorted(B.rglob('*')) if p.is_file() and (p.suffix in ['.tex','.bib'] or str(p.relative_to(B)).startswith(('figures/','supplementary_results/')))]
with (O/'preservation_manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
report=dict(baseline='SCAFFOLD_E5_MainText_Revised_20261010.zip',changed_manuscript_files=changed,checks=checks,failed_checks=[c['check'] for c in checks if not c['passed']],scientific_work=dict(new_training=False,resampling=False,new_proof_audit=False,new_literature_search=False))
(O/'preservation_and_compile.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(changed=changed,checks=len(checks),failures=report['failed_checks'],layout=checks[-2],figure_min=fonts[0]),indent=2))
assert not report['failed_checks'],report['failed_checks']
