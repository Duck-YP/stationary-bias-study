from pathlib import Path
import argparse, re, json, csv, hashlib, difflib
from decimal import Decimal
import fitz
from pypdf import PdfReader

ap=argparse.ArgumentParser()
ap.add_argument('--before',type=Path,required=True)
ap.add_argument('--after',type=Path,required=True)
args=ap.parse_args();B=args.before;A=args.after
out=A/'revision_audit/presentation_dedup_20261012';out.mkdir(parents=True,exist_ok=True)
checks=[]
def ck(k,p,**info):
    checks.append(dict(check=k,passed=bool(p),**info))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tbl(s,label):
    for m in re.finditer(r'\\begin\{table\}(?:\[[^\]]*\])?[\s\S]*?\\end\{table\}',s):
        if r'\label{'+label+'}' in m.group():return m.group()
    raise ValueError(label)
def read(p):return p.read_text()

changed=['sections/01_introduction.tex','sections/08_discussion_limitations.tex',
         'sections/07_numerical_study.tex','appendix/C_numerical_details.tex']
fixed=['main.tex','macros.tex','references.bib','main.bbl',
       'sections/02_related_work.tex','sections/03_setting_preliminaries.tex',
       'sections/04_main_results.tex','sections/05_mechanism.tex','sections/09_conclusion.tex',
       'appendix/A_scaffold_proof.tex','appendix/B_fedavg_proof.tex','appendix/D_reproducibility.tex']
for f in fixed:ck('unchanged:'+f,sha(B/f)==sha(A/f))
for f in changed:ck('edited:'+f,sha(B/f)!=sha(A/f))
for dirname in ['figures','supplementary_results']:
    count=0
    for p in (B/dirname).rglob('*'):
        if p.is_file():
            rel=p.relative_to(B);ck('preserved:'+str(rel),(A/rel).exists() and sha(p)==sha(A/rel));count+=1
    print(dirname,'unchanged baseline files',count)

oldC=read(B/'appendix/C_numerical_details.tex');newC=read(A/'appendix/C_numerical_details.tex');newN=read(A/'sections/07_numerical_study.tex')
# Numeric main coefficient display and original interval supplement.
oldrows=[]
for l in tbl(oldC,'tab:num-core').splitlines():
    if re.match(r'^[SFD] & [PS] & [24] & [12] & ',l):
        oldrows.append([x.strip().strip('$') for x in l.removesuffix(r'\\').split('&')])
mainrows=[]
for l in tbl(newN,'tab:num-attribution-summary').splitlines():
    if l.startswith((r'\Scaf{} &',r'\FedAvg{} &','Paired difference &')):
        c=[x.strip() for x in l.removesuffix(r'\\').split('&')];mainrows.append(c)
ck('main_coefficient_vectors_9',len(mainrows)==9)
nm={r'\Scaf{}':'S',r'\FedAvg{}':'F','Paired difference':'D'}
oldmap={(r[0],r[2],r[1],r[3]):r for r in oldrows}
for rr in mainrows:
    st=nm[rr[0]];h,g=rr[1:3]
    for col,oldcol in [(3,5),(4,4)]:
        v=re.findall(r'-?\d+\.\d+',rr[col])
        for j,val in enumerate(v,1):
            expected=Decimal(oldmap[st,h,g,str(j)][oldcol]).quantize(Decimal('0.0000001'))
            ck(f'coefficient_rounding:{st}:{h}:{g}:{j}:{col}',Decimal(val)==expected)
for l in tbl(newC,'tab:num-core').splitlines():
    if re.match(r'^[SFD] & [24] & [PS] & ',l):
        c=[x.strip().strip('$') for x in l.removesuffix(r'\\').split('&')]
        for j in [1,2]:ck(f'original_interval:{c[:3]}:{j}',c[j+2]==oldmap[c[0],c[1],c[2],str(j)][6])
ck('CI_table_has_no_point_target_columns','Theory' not in tbl(newC,'tab:num-core') and r'\widehat\beta' not in tbl(newC,'tab:num-core'))
# New preservation CSV retains full record precision.
with (A/'supplementary_results/presentation_source/historical_coefficient_intercepts.csv').open() as f:src=list(csv.DictReader(f))
ck('archive_has_all_18_records',len(src)==18)
for r in src:
    x=oldmap[r['study'],r['H'],r['grid'],r['coordinate']]
    ck('source_precision:'+str(x[:4]),r['estimate']==x[4] and r['target']==x[5] and '['+r['ci_lower']+','+r['ci_upper']+']'==x[6])
# E5 full six records, only the order of the metric columns changes.
eold=[];enew=[]
for s,dest in [(tbl(oldC,'tab:e5-bridge'),eold),(tbl(newN,'tab:e5-bridge'),enew)]:
    for l in s.splitlines():
        if re.match(r'^[24] & ',l):dest.append([x.strip() for x in l.removesuffix(r'\\').split('&')])
ck('E5_has_six_main_records',len(enew)==6)
for o,n in zip(eold,enew):ck('E5_record:'+str(o[:4]),n==o[:4]+[o[5],o[4],o[6]])
ck('E5_table_only_in_main',newN.count(r'\label{tab:e5-bridge}')==1 and r'\label{tab:e5-bridge}' not in newC)
# Retained additional E4 rows unchanged; intervals of removed points remain in original data.
ot=tbl(oldC,'tab:e4-primary');nt=tbl(newC,'tab:e4-primary')
for prefix in [r'$\widehat M_K$', 'Train objective gap', 'Held-out log loss',r'$\Delta\widehat U_K$',r'$\Delta\widehat V_K$']:
    os=next(x.strip() for x in ot.splitlines() if x.strip().startswith(prefix+' &'))
    ns=next(x.strip() for x in nt.splitlines() if x.strip().startswith(prefix+' &'))
    ck('E4_retained:'+prefix,os==ns)
ck('E4_K64_U_V_shares_not_reprinted',all(x not in nt for x in [r'$\widehat U_K$ &',r'$\widehat V_K$ &',r'$100\widehat U_K/\widehat M_K$ &',r'$\Delta\widehat M_K$ &']))
# R0 extra metrics correctly pivoted; R1/R2 full rows unchanged.
rt=tbl(oldC,'tab:supp-real-full');rn=tbl(newC,'tab:supp-real-full')
r0={}
for l in rt.splitlines():
    if re.match(r'^R[012] & ',l):
        c=[x.strip() for x in l.removesuffix(r'\\').split('&')]
        if c[0]=='R0':r0[c[1],c[2]]=c
        else:ck('R1R2:'+str(c[:3]),l in rn)
for n in ['8','32','128']:
    exp=' & '.join([n,r0[n,'S'][5],r0[n,'F'][5],r0[n,'S'][6],r0[n,'F'][6]])+' '+r'\\'
    ck('R0_extra_metrics:'+n,exp in rn)
ck('R0_projections_not_reprinted',not re.search(r'^R0 & ',rn,re.M))
# Everything else in the complete table payload remains verbatim.
for lab in ['tab:E-h4diag','tab:E-d5','tab:E-direct-balance','tab:supp-leading']:
    ck('unchanged_unique_table:'+lab,tbl(oldC,lab)==tbl(newC,lab))
oldN=read(B/'sections/07_numerical_study.tex')
for lab in ['tab:supp-control','tab:supp-policy']:
    ck('unchanged_main_table:'+lab,tbl(oldN,lab)==tbl(newN,lab))
# Source labels and figure references (active manuscript inputs only).
rels=['main.tex','macros.tex']+[str(x.relative_to(A)) for d in ['sections','appendix'] for x in sorted((A/d).glob('*.tex'))]
def active_text(root):return '\n'.join(re.sub(r'(?<!\\)%[^\n]*','',read(root/p)) for p in rels)
sa=active_text(A);sb=active_text(B)
labels=re.findall(r'\\label\{([^}]+)\}',sa)
oldlabels=re.findall(r'\\label\{([^}]+)\}',sb)
ck('no_duplicate_active_labels',len(labels)==len(set(labels)))
ck('all_prior_labels_retained',set(oldlabels).issubset(labels))
ck('E5_active_table_label_once',labels.count('tab:e5-bridge')==1)
figa=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',sa)
figb=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',sb)
ck('same_nine_active_panels',len(figa)==9 and sorted(figa)==sorted(figb))
# Diagnostic statements cannot disappear with redundancy removal.
for term in ['144','0.0054372','0.0013633','48-seed','132','48 strict','0.08365',r'$[2.7415,3.1125]$',r'$[2.7101,3.1439]$',r'$[2.6928,3.1919]$','0.872197','1.8553','1.8907']:
    ck('retained_diagnostic:'+term,term in sa)
# PDF/log QA and final figure font size.
P=fitz.open(A/'main.pdf');alltext='\n'.join(p.get_text() for p in P)
rs=next(i for i,p in enumerate(P) if p.get_text().startswith('References\n'))
as_=next(i for i,p in enumerate(P) if p.get_text().startswith('A\nCommon moment estimates'))
layout={'pages':len(P),'main_pages':rs,'reference_pages':as_-rs,'appendix_pages':len(P)-as_}
ck('pdf_no_unresolved_refs','??' not in alltext)
log=read(A/'main.log');warnings=re.findall(r'^.*(?:Warning|Overfull|Underfull|Error).*$',log,re.M)
ck('no_compile_or_box_warnings',not warnings,warnings=warnings)
reader=PdfReader(str(A/'main.pdf'));placed=[]
for i,p in enumerate(P):
    blocks=p.get_text('dict')['blocks'];pg=reader.pages[i]
    xo=pg['/Resources'].get('/XObject',{})
    if hasattr(xo,'get_object'):xo=xo.get_object()
    ctm=fitz.Matrix(1,1);stack=[]
    for operands,operator in pg.get_contents().operations:
        if operator==b'q':stack.append(fitz.Matrix(ctm))
        elif operator==b'Q':ctm=stack.pop()
        elif operator==b'cm':ctm=fitz.Matrix(*(float(v) for v in operands))*ctm
        elif operator==b'Do':
            obj=xo[operands[0]].get_object()
            if obj.get('/Subtype')!='/Form':continue
            box=fitz.Rect([float(v) for v in obj['/BBox']]);mat=fitz.Matrix(*(float(v) for v in obj.get('/Matrix',[1,0,0,1,0,0])))
            rect=box*mat*ctm*p.transformation_matrix
            spans=[s for b in blocks if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip() and rect.contains(fitz.Rect(s['bbox']))]
            if spans:placed.append({'page':i+1,'xobject':str(operands[0]),'min_final_pdf_font_pt':min(s['size'] for s in spans),'width_pdf_pt':rect.width})
ck('nine_panels_min_9pt',len(placed)==9 and all(p['min_final_pdf_font_pt']>=9 for p in placed))
ck('same_size_tables_and_body_no_global_shrink',sha(A/'macros.tex')==sha(B/'macros.tex') and sha(A/'main.tex')==sha(B/'main.tex'))
report={'baseline':'SCAFFOLD_Full_Updated_20261010.zip','layout':layout,'checks':checks,'check_count':len(checks),'failures':[c for c in checks if not c['passed']],'new_training':False,'new_resampling':False,'new_proof_audit':False,'min_figure_font_pdf_pt':min(p['min_final_pdf_font_pt'] for p in placed)}
(out/'preservation_and_layout.json').write_text(json.dumps(report,indent=2))
with (out/'figure_font_audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(placed[0]));w.writeheader();w.writerows(placed)
diffs=[]
for f in changed:diffs+=list(difflib.unified_diff(read(B/f).splitlines(True),read(A/f).splitlines(True),fromfile='before/'+f,tofile='after/'+f))
(out/'manuscript_changes.diff').write_text(''.join(diffs))
(out/'final_compile.log').write_bytes((A/'main.log').read_bytes())
(out/'final_bibtex.log').write_bytes((A/'main.blg').read_bytes())
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
assert not report['failures'],report['failures']
