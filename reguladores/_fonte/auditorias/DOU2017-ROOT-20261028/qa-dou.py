from pathlib import Path
import sys,runpy
root=Path.cwd().resolve();target=Path(sys.argv[1]).resolve();assert root/'reguladores/_fonte/auditorias' in target.parents and target.suffix=='.py'
sys.path[:0]=[str(target.parent),str(root/'scripts/bin/qa-20261027/python'),str(root/'scripts/bin/qa-html5-20261027/python')];sys.argv=[str(target),*sys.argv[2:]];runpy.run_path(str(target),run_name='__main__')
