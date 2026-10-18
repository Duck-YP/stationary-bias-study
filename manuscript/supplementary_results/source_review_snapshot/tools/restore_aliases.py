"""Restore only byte-identical partition diagnostic aliases after extraction."""
from pathlib import Path
import argparse
import csv
import hashlib
import shutil


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    core=bundle/'REVIEW_CORE'
    restored=0
    with (core/'PARTITION_DIAGNOSTIC_ALIASES.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            source=(bundle/row['canonical_export_path']).resolve()
            target=(core/row['original_path']).resolve()
            assert source.is_relative_to(core) and target.is_relative_to(core)
            assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
            if source==target:
                continue
            if target.exists():
                assert hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256']
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target)
                restored+=1
    print(f'Restored {restored} byte-identical aliases; no training or analysis performed.')


if __name__=='__main__':
    main()
