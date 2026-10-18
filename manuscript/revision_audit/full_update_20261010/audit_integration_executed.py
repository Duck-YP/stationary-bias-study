from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import re, json, hashlib, csv
import fitz

W=Path('/mnt/data/scaffold_full_update_20261010')
R=W/'manuscript'
A=R/'revision_audit/full_update_20261010'
Z=ZipFile('/mnt/data/SCAFFOLD_Narrative_Refined_20261010.zip')
checks=[]
def active(text):
    return '\n'.join(re.sub(r'(?<!\\)%.*','',line) for line in text.splitlines())
def ck(name, ok, **data):
    checks.append(dict(check=name,passed=bool(ok),**data))
def sha(blob): return hashlib.sha256(blob).hexdigest()
source_files=['main.tex','macros.tex']+[str(p.relative_to(R)) for folder in ['sections','appendix'] for p in sorted((R/folder).glob('*.tex'))]
before='\n'.join(active(Z.read('manuscript/'+p).decode()) for p in source_files)
after='\n'.join(active((R/p).read_text()) for p in source_files)
expected=['sections/01_introduction.tex','sections/02_related_work.tex','sections/07_numerical_study.tex','sections/08_discussion_limitations.tex']
changed=[p for p in source_files if Z.read('manuscript/'+p)!=(R/p).read_bytes()]
ck('exactly_four_agreed_manuscript_files_changed',set(changed)==set(expected),files=changed)
for folder in ['appendix/','figures/','supplementary_results/']:
    files=[n for n in Z.namelist() if n.startswith('manuscript/'+folder) and not n.endswith('/')]
    bad=[n for n in files if Z.read(n)!=(W/n).read_bytes()]
    ck('byte_preservation_'+folder,not bad,count=len(files),changed=bad)
for p in ['main.tex','macros.tex','references.bib','main.bbl','build.sh','sections/03_setting_preliminaries.tex','sections/04_main_results.tex','sections/05_mechanism.tex','sections/09_conclusion.tex']:
    ck('byte_preservation_'+p,Z.read('manuscript/'+p)==(R/p).read_bytes())
for env in ['theorem','corollary','proposition','lemma','proof','equation','align','figure']:
    pat=r'\\begin\{'+env+r'\}(?:\[[^\]]*\])?.*?\\end\{'+env+r'\}'
    x,y=re.findall(pat,before,re.S),re.findall(pat,after,re.S)
    ck('preserved_'+env,x==y,count=len(x),new_count=len(y))
ck('unnumbered_display_math_preserved',re.findall(r'\\\[.*?\\\]',before,re.S)==re.findall(r'\\\[.*?\\\]',after,re.S))
pat=r'\\begin\{table\}(?:\[[^\]]*\])?.*?\\end\{table\}'
bt,at=re.findall(pat,before,re.S),re.findall(pat,after,re.S)
ck('tables_other_than_Table1_preserved',bt[1:]==at[1:],total=len(at),table1_changed=bt[0]!=at[0])
labels=re.findall(r'\\label\{([^}]+)\}',after)
old_labels=re.findall(r'\\label\{([^}]+)\}',before)
ck('no_duplicate_active_labels',len(labels)==len(set(labels)),count=len(labels))
ck('old_labels_preserved',not(set(old_labels)-set(labels)),added=sorted(set(labels)-set(old_labels)))
refs=[label for group in re.findall(r'\\(?:eqref|ref|cref|Cref|pageref)\{([^}]+)\}',after) for label in group.split(',')]
missing=sorted(set(refs)-set(labels))
ck('all_source_references_resolve',not missing,missing=missing)
cp=r'\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}'
keys=lambda s:{k.strip() for g in re.findall(cp,s) for k in g.split(',')}
ck('citation_key_set_preserved',keys(before)==keys(after),keys=sorted(keys(after)))
num_before=active(Z.read('manuscript/sections/07_numerical_study.tex').decode())
num_after=active((R/'sections/07_numerical_study.tex').read_text())
math_tokens=lambda s: Counter(re.findall(r'(?<!\\)\$([^$]+)(?<!\\)\$',s))
ck('all_numerical_section_inline_math_preserved',math_tokens(num_before)==math_tokens(num_after))
ck('single_significance_paragraph',active((R/'sections/01_introduction.tex').read_text()).count('\\paragraph{Significance and scope.}')==1)
new_headings=re.findall(r'\\(subsection|subsubsection)\{([^}]+)\}',num_after)
ck('controlled_group_has_four_subsubsections',sum(kind=='subsubsection' for kind,_ in new_headings)==4,headings=new_headings)
log=(R/'main.log').read_text(errors='replace')
issues=[line for line in log.splitlines() if re.search(r'Warning|Overfull|Underfull|undefined|multiply defined|^!',line)]
ck('final_latex_log_clean',not issues,issues=issues)
blg=(R/'main.blg').read_text(errors='replace')
ck('bibtex_no_errors',not re.search(r'Warning--|I couldn.t|error message|empty ',blg))
P=fitz.open(R/'main.pdf')
ref_start=next(i for i,p in enumerate(P) if p.get_text().startswith('References\n'))
app_start=next(i for i,p in enumerate(P) if p.get_text().startswith('A\nCommon moment estimates'))
layout=dict(pages=len(P),main_pages=ref_start,reference_pages=app_start-ref_start,appendix_pages=len(P)-app_start)
# Confirm that updated reference text and grouped headings appear in the compiled PDF.
alltext='\n'.join(p.get_text() for p in P)
ck('compiled_new_sections_present','Controlled tests of analytical predictions' in alltext and 'Significance and scope.' in alltext)
ck('compiled_no_unresolved_placeholders','??' not in alltext)
font=[]
for path in sorted((R/'figures/redrawn').glob('*.pdf')):
    d=fitz.open(path)
    fs=[s['size'] for b in d[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
    font.append({'panel':path.name,'source_min_font_pdf_pt':min(fs),'source_width_pdf_pt':d[0].rect.width})
# Locate final figure placements by parsing the page graphics-state stack.
# get_xobjects returns the form's local BBox, not its page placement.
from pypdf import PdfReader
reader=PdfReader(str(R/'main.pdf'))
placed=[]
for i,p in enumerate(P):
    blocks=p.get_text('dict')['blocks']
    pg=reader.pages[i]
    xobjects=pg['/Resources'].get('/XObject',{})
    if hasattr(xobjects,'get_object'): xobjects=xobjects.get_object()
    ctm=fitz.Matrix(1,1); stack=[]
    for operands,operator in pg.get_contents().operations:
        if operator==b'q':
            stack.append(fitz.Matrix(ctm))
        elif operator==b'Q':
            ctm=stack.pop()
        elif operator==b'cm':
            ctm=fitz.Matrix(*(float(v) for v in operands))*ctm
        elif operator==b'Do':
            name=operands[0]
            obj=xobjects[name].get_object()
            if obj.get('/Subtype')!='/Form': continue
            bbox=fitz.Rect([float(v) for v in obj['/BBox']])
            matrix=fitz.Matrix(*(float(v) for v in obj.get('/Matrix',[1,0,0,1,0,0])))
            rect=bbox*matrix*ctm*p.transformation_matrix
            spans=[s for b in blocks if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip() and rect.contains(fitz.Rect(s['bbox']))]
            if spans:
                placed.append({'page':i+1,'xobject':str(name),'minimum_final_font_pdf_pt':min(s['size'] for s in spans),'text_spans':len(spans),'placement_width_pdf_pt':rect.width})
ck('nine_final_figure_panels_meet_9pt',len(placed)==9 and all(d['minimum_final_font_pdf_pt']>=9 for d in placed),placements=placed)
(A/'preservation_and_compile.json').write_text(json.dumps({'baseline':'SCAFFOLD_Narrative_Refined_20261010.zip','layout':layout,'checks':checks,'failed_checks':[c['check'] for c in checks if not c['passed']],'new_training':False,'new_resampling':False,'new_proof_audit':False},indent=2))
with (A/'figure_font_audit.csv').open('w') as f:
    dw=csv.DictWriter(f,fieldnames=list(placed[0]));dw.writeheader();dw.writerows(placed)
(A/'final_compile.log').write_bytes((R/'main.log').read_bytes())
(A/'final_bibtex.log').write_bytes((R/'main.blg').read_bytes())
print(json.dumps({'layout':layout,'checks':len(checks),'failed':[c['check'] for c in checks if not c['passed']],'font_min':min(d['minimum_final_font_pdf_pt'] for d in placed)},indent=2))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
