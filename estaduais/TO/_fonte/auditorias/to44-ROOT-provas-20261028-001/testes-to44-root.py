from pathlib import Path
import sys,unittest
r=Path.cwd();sys.path[:0]=[str(r/'estaduais/TO/_fonte/auditorias/qa-fontes-20261028-001/fonttools-4.60.1-py3-none-any.whl'),str(r/'scripts/estados/snapshots/to_pdf_simples_20261028_008'),str(r/'scripts/estados/snapshots/to_promocao_20261028_001'),str(r/'scripts/bin/qa-20261027/python')]
l=unittest.TestLoader();suite=unittest.TestSuite()
for dirname in ['to_pdf_simples_20261028_008','to_promocao_20261028_001']:
 for p in sorted((r/'scripts/estados/snapshots'/dirname).glob('test_*.py')):suite.addTests(l.loadTestsFromName(p.stem))
res=unittest.TextTestRunner(verbosity=1).run(suite);assert res.wasSuccessful() and res.testsRun==97
