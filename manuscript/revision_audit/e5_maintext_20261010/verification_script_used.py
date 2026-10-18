from pathlib import Path
import re, csv, json, hashlib, difflib, math
import fitz
root=Path('/mnt/data/e5_maintext_revision_20261010')
b=root/'baseline/manuscript'; m=root/'manuscript'
qa=m/'revision_audit/e5_maintext_20261010'; qa.mkdir(parents=True,exist_ok=True)
strip=lambda s:re.sub(r'(?<!\\)%[^\n]*','',s)
files=[Path('main.tex'),Path('macros.tex')]+[Path('sections')/p.name for p in sorted((m/'sections').glob('*.tex'))]+[Path('appendix')/p.name for p in sorted((m/'appendix').glob('*.tex'))]
labels={};refs=[];bad_eqrefs=[]
for p in files:
    s=strip((m/p).read_text())
    for l in re.findall(r'\\label\{([^}]+)\}',s): labels.setdefault(l,[]).append(str(p))
    for match in re.finditer(r'\\(?:ref|eqref|[Cc]ref|autoref)\{([^}]+)\}',s):
        for r in match[1].split(','):refs.append((str(p),r.strip()))
    for mt in re.finditer(r'\\eqref\{',s):
        preceding=s[max(0,mt.start()-150):mt.start()]
        # Existing multi-equation references can be separated by and/range.
        if not re.search(r'Equations?[\s~]',preceding): bad_eqrefs.append((str(p),s[mt.start():mt.start()+50]))
missing=[x for x in refs if x[1] not in labels]
dups={k:v for k,v in labels.items() if len(v)>1}
assert not missing,missing
assert not dups,dups
assert not bad_eqrefs,bad_eqrefs
all_active='\n'.join(strip((m/p).read_text()) for p in files)
assert not re.search(r'\bef\{(?:sec|app):',all_active)

# Mathematical statement and table preservation.
protected=['sections/02_related_work.tex','sections/03_setting_preliminaries.tex','sections/04_main_results.tex','sections/05_mechanism.tex','appendix/A_scaffold_proof.tex','appendix/B_fedavg_proof.tex','appendix/D_reproducibility.tex','macros.tex','references.bib']
preserved={p:(b/p).read_bytes()==(m/p).read_bytes() for p in protected}
assert all(preserved.values())
tables=[]
for p in files:
    find=lambda x:re.findall(r'\\begin\{table\}.*?\\end\{table\}',strip(x),re.S)
    old=find((b/p).read_text());new=find((m/p).read_text())
    assert old==new,p
    if old:tables.append({'file':str(p),'count':len(old),'unchanged':True})
proxy=lambda s:re.search(r'\\begin\{equation\}\s*\\label\{eq:e5-proxy\}.*?\\end\{equation\}',s,re.S).group(0)
assert proxy((b/'appendix/C_numerical_details.tex').read_text())==proxy((m/'sections/07_numerical_study.tex').read_text())

figpaths=[p.relative_to(b) for p in (b/'figures').rglob('*') if p.is_file()]
supppaths=[p.relative_to(b) for p in (b/'supplementary_results').rglob('*') if p.is_file()]
assert all((b/p).read_bytes()==(m/p).read_bytes() for p in figpaths)
assert all((b/p).read_bytes()==(m/p).read_bytes() for p in supppaths)
for sec in ['sections/07_numerical_study.tex','appendix/C_numerical_details.tex']:
    figures=lambda s:re.findall(r'\\begin\{figure\}.*?\\end\{figure\}',strip(s),re.S)
    assert figures((b/sec).read_text())==figures((m/sec).read_text())

# Recheck numeric summaries introduced into the main text; no refit/resample.
with (m/'supplementary_results/E5/FULL_VECTOR_ALIGNMENT.csv').open() as f:
    cells=[r for r in csv.DictReader(f) if int(r['K'])==64 and int(r['H'])>1]
assert len(cells)==6 and all(int(r['dimension'])==124 for r in cells)
ranges={key:[min(float(r[key]) for r in cells),max(float(r[key]) for r in cells)] for key in ['cosine','norm_ratio','projection_ratio','relative_residual']}
assert [f'{v:.4f}' for v in ranges['cosine']]==['0.9965','0.9993']
assert [f'{v:.3f}' for v in ranges['norm_ratio']]==['0.718','0.940']
assert max(float(r['norm_ratio']) for r in cells)<1
with (m/'supplementary_results/E5/SCALING_COMPARISONS.csv').open() as f:
    hs=[r for r in csv.DictReader(f) if int(r['K'])==64 and r['kind']=='H']
assert len(hs)==1
assert f"{float(hs[0]['projection_ratio']):.3f}"=='2.927'
assert math.isclose(float(hs[0]['proxy_ratio']),3.5)
with (m/'supplementary_results/E5/NEGATIVE_CONTROLS.csv').open() as f:
    comps=[r for r in csv.DictReader(f) if int(r['K'])==64 and int(r['H'])>1 and r['cosine']]
comp_ranges={}
for cmp in ['frozen_x_ref','negative_T_Sigma']:
    vals=[float(r['cosine']) for r in comps if r['comparator']==cmp]
    assert len(vals)==6
    comp_ranges[cmp]=[min(vals),max(vals)]

# Same intrinsic figure sizes and same LaTeX widths; recompute final-size fonts.
font_rows=[]
with (b/'revision_audit/figure_font_audit.csv').open() as f:
    for r in csv.DictReader(f):
        doc=fitz.open(m/'figures/redrawn'/r['panel'])
        fonts=[sp['size'] for bl in doc[0].get_text('dict')['blocks'] if 'lines' in bl for ln in bl['lines'] for sp in ln['spans'] if sp.get('text','').strip()]
        w=doc[0].rect.width
        # TeX pt and PDF bp use different inch definitions.
        scale=float(r['placed_width_tex_pt'])*72/72.27/w
        final=min(fonts)*scale
        assert final>=9
        font_rows.append({'panel':r['panel'],'source_min_pdf_pt':min(fonts),'latex_scale':scale,'final_min_pdf_pt':final,'pass_min9':True})
with (qa/'figure_font_audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=font_rows[0].keys());w.writeheader();w.writerows(font_rows)

log=(m/'main.log').read_text(errors='replace')
issues=[x for x in log.splitlines() if re.search(r'LaTeX Warning|Package .+ Warning|Overfull|Underfull|^!|undefined references|multiply defined',x)]
assert not issues,issues
pdf=fitz.open(m/'main.pdf')
ref_start=next(i+1 for i,p in enumerate(pdf) if re.match(r'^References\s',p.get_text()))
app_start=next(i+1 for i,p in enumerate(pdf) if 'A\nCommon moment estimates' in p.get_text())
text='\n'.join(p.get_text() for p in pdf)
assert 'Directional agreement beyond the additive-noise model' in text
assert 'efsec:num-averaging' not in text and 'efapp:e4-averaging' not in text
abstract=(m/'main.tex').read_text().split('\\begin{abstract}')[1].split('\\end{abstract}')[0]
summary={'baseline_zip':'SCAFFOLD_Final_E4_E5_20261010.zip','baseline_pages':37,'pages':len(pdf),'main_text_pages':ref_start-1,'reference_pages':app_start-ref_start,'appendix_pages':len(pdf)-app_start+1,'abstract_whitespace_word_count':len(abstract.split()),'protected_files_unchanged':preserved,'tables_unchanged':tables,'total_unchanged_tables':sum(t['count'] for t in tables),'unchanged_figure_files':len(figpaths),'unchanged_supplementary_files':len(supppaths),'active_panels':len(font_rows),'labels':len(labels),'references':len(refs),'undefined_references':missing,'duplicate_labels':dups,'bare_equation_refs':bad_eqrefs,'latex_issues':issues,'e5_proxy_equation_relocated_unchanged':True,'E5_K64_nonzero_proxy_cells':len(cells),'E5_numeric_ranges':ranges,'E5_reference_direction_ranges':comp_ranges,'E5_H_ratio':float(hs[0]['projection_ratio']),'E5_H_proxy_ratio':float(hs[0]['proxy_ratio']),'figure_final_min_pt':min(r['final_min_pdf_pt'] for r in font_rows),'new_training':False,'new_bootstrap':False,'new_proof_audit':False}
(qa/'revision_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
# The text diff intentionally excludes generated outputs, unchanged evidence,
# and historical notes, and shows exactly the six modified manuscript files.
changed=[];diff=[]
for p in files:
    old=(b/p).read_text();new=(m/p).read_text()
    if old!=new:
        changed.append(str(p))
        diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+str(p),tofile='after/'+str(p)))
(qa/'manuscript_changes.diff').write_text(''.join(diff))
summary['changed_manuscript_files']=changed
(qa/'revision_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['pages','main_text_pages','reference_pages','appendix_pages','total_unchanged_tables','unchanged_figure_files','unchanged_supplementary_files','active_panels','figure_final_min_pt','changed_manuscript_files']},indent=2))
