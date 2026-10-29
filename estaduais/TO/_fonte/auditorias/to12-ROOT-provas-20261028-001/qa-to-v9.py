from pathlib import Path
import sys,runpy
r=Path.cwd();target=Path(sys.argv[1]).resolve();assert r/'scripts/estados/snapshots' in target.parents
sys.path[:0]=[str(r/'estaduais/TO/_fonte/auditorias/qa-fontes-20261028-001/fonttools-4.60.1-py3-none-any.whl'),str(target.parent),str(r/'scripts/estados/snapshots/to_pdf_simples_20261028_009'),str(r/'scripts/estados/snapshots/to_promocao_20261028_001'),str(r/'scripts/bin/qa-20261027/python')];sys.argv=[str(target),*sys.argv[2:]];runpy.run_path(str(target),run_name='__main__')
