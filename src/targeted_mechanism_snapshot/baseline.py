"""Read-only baseline inventory; all outputs stay in this new directory."""
import hashlib, json, pathlib, platform, subprocess, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files = {}
    for base in ('manuscript', 'supplementary_study/study'):
        for p in sorted((REPO/base).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                files[p.relative_to(REPO).as_posix()] = {'sha256':sha(p), 'size':p.stat().st_size}
    diff = []
    archive = pathlib.Path(r'original_attachments/Characterizing_Client_Independent_Stationary_Bias_for_SCAFFOLD_and_FedAvg_in_Federated_Learning.zip')
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            for e in z.infolist():
                if e.filename.startswith('manuscript/') and not e.is_dir():
                    p=REPO/e.filename
                    if not p.exists() or sha(p)!=hashlib.sha256(z.read(e)).hexdigest(): diff.append(e.filename)
    result={'files':files,'latest_supplied_archive':str(archive),'local_changes_vs_supplied_archive':diff,
            'baseline_policy':'Current local files authoritative; do not overwrite. No historical commit inferred.',
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            'python':sys.version,'platform':platform.platform()}
    (ROOT/'BASELINE_MANIFEST.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'files':len(files),'local_changes':diff},indent=2))
if __name__=='__main__': main()
