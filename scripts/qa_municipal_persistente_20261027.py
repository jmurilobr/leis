"""Executa QA congelado com dependências persistentes, inclusive sob Python -I."""
import argparse
import importlib.metadata
from pathlib import Path
import runpy
import sys
ROOT=Path(__file__).resolve().parent.parent
RUNTIME=ROOT/'scripts/bin/qa-20261027/python'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('script',type=Path)
    ap.add_argument('argumentos',nargs=argparse.REMAINDER)
    a=ap.parse_args()
    target=a.script.resolve()
    if ROOT/'scripts' not in target.parents or target.suffix!='.py':raise ValueError('Somente script explícito deste repositório')
    if not (RUNTIME/'markdown_it').is_dir():raise RuntimeError('Runtime QA persistente ainda indisponível')
    sys.path.insert(0,str(RUNTIME))
    for package,version in [('markdown-it-py','4.0.0'),('mdurl','0.1.2')]:
        if importlib.metadata.version(package)!=version:raise RuntimeError('Versão QA divergente: '+package)
    sys.argv=[str(target)]+a.argumentos
    runpy.run_path(str(target),run_name='__main__')

if __name__=='__main__':main()
