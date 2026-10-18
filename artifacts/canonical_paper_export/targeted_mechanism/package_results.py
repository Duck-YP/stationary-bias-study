"""Build bounded review and source bundles without changing master manuscript."""
import csv,hashlib,json,pathlib,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_baseline():
    base=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
    altered=[]; missing=[]
    for rel,meta in base['files'].items():
        p=REPO/rel
        if not p.exists(): missing.append(rel)
        elif sha(p)!=meta['sha256']: altered.append(rel)
    result={'checked_files':len(base['files']),'changed_files':altered,'missing_files':missing,
            'manuscript_and_historical_source_unchanged':not altered and not missing}
    (ROOT/'BASELINE_AFTER_CHECK.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    if altered or missing: raise RuntimeError(result)
    return result
def main():
    baseline=verify_baseline()
    # Final source and local retrieval manifests include all observed failures.
    local=[]
    for phase in ['pilot','production']:
        for p in sorted((ROOT/'local'/phase).rglob('*.npz')):
            local.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    for p in sorted((ROOT/'literature/sources').rglob('*')):
        if p.is_file(): local.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    (ROOT/'LOCAL_ARTIFACT_MANIFEST.json').write_text(json.dumps(local,indent=2),encoding='utf8')
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*.py') if not any(x in p.parts for x in ['local','sources','scratch'])}
    (ROOT/'FINAL_SOURCE_HASHES.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf8')
    review=[]; source=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(x in rel.parts for x in ['__pycache__','local','sources','scratch','.pytest_cache']): continue
        if p.suffix.lower()=='.zip' or p.name=='DELIVERY_MANIFEST.json': continue
        # Code also accompanies the review; full independent source bundle below.
        review.append((p,rel.as_posix()))
        if p.suffix.lower() in ['.py','.md','.json','.patch','.tex','.bib','.txt','.lock']:
            if rel.parts[0] not in ['results'] or p.name=='execution_diagnostics.json': source.append((p,rel.as_posix()))
    # Small complete per-run summaries; trajectories are not stored.
    for phase in ['pilot','production']:
        for p in sorted((ROOT/'local'/phase).glob('*/seed_*/result.npz')):
            review.append((p,'run_summaries/'+p.relative_to(ROOT/'local').as_posix()))
    # Current historical test source is supplied, explicitly not the missing freeze.
    for p in sorted((REPO/'supplementary_study/study').glob('*.py')):
        source.append((p,'historical_current_source/study/'+p.name))
    source.append((REPO/'supplementary_study/requirements.lock','historical_current_source/requirements.lock'))
    packages=[]
    for name,files in [('TARGETED_MECHANISM_REVIEW.zip',review),('SOURCE_TARGETED_MECHANISM.zip',source)]:
        path=ROOT/name
        manifest={arc:{'bytes':p.stat().st_size,'sha256':sha(p)} for p,arc in files}
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p,arc in files: z.write(p,arc)
            z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for arc,m in manifest.items(): assert hashlib.sha256(z.read(arc)).hexdigest()==m['sha256']
        packages.append({'file':name,'bytes':path.stat().st_size,'sha256':sha(path),'entries':len(files)+1,'crc_and_sha256_verified':True})
    assert packages[0]['bytes']<50*1024**2
    (ROOT/'DELIVERY_MANIFEST.json').write_text(json.dumps({'packages':packages,'baseline':baseline},indent=2),encoding='utf8')
    print(json.dumps(packages,indent=2))
if __name__=='__main__': main()
