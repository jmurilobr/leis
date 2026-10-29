from pathlib import Path
import sys,json,unittest,tempfile
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[3];sys.dont_write_bytecode=True;sys.path.insert(0,str(B/'codigo/scripts'));sys.path.insert(0,str(B));import versoes_exportadas as versions
class Isolamento(unittest.TestCase):
 def test_importacoes_usam_export_sem_globals(self):
  import html2md,baixar_federal,comum,preparar_lote_decretos_cache
  for mod,logical in [(html2md,'scripts/html2md.py'),(baixar_federal,'scripts/baixar_federal.py'),(comum,'scripts/comum.py'),(preparar_lote_decretos_cache,'scripts/preparar_lote_decretos_cache.py')]:
   self.assertEqual(Path(mod.__file__).resolve(),versions.arquivo_logico(logical).resolve());self.assertNotEqual(Path(mod.__file__).resolve(),(R/logical).resolve())
 def test_codigo_sem_mapeamento_nao_cai_no_global(self):
  with self.assertRaises(AssertionError):versions.arquivo_logico('scripts/modulo_nao_declarado.py')
 def test_codigo_alterado_rejeitado_antes_importacao(self):
  original=versions.arquivo_logico('scripts/html2md.py');expected=versions.sha(original.read_bytes())
  with tempfile.TemporaryDirectory(dir=B)as folder:
   target=Path(folder)/'html2md.py';target.write_bytes(original.read_bytes()+b'\n# simulacao de alteracao\n');fake={'versoes_logicas':{'scripts/html2md.py':{'path_exportado':str(target.relative_to(R)),'sha256_original_esperado':expected}}}
   with patch.object(versions,'mapa',return_value=fake):
    with self.assertRaises(AssertionError):versions.arquivo_logico('scripts/html2md.py')
 def test_symlink_de_insumo_nao_mapeado_rejeitado(self):
  with tempfile.TemporaryDirectory(dir=B)as folder:
   d=Path(folder);(d/'real').write_bytes(b'fonte');(d/'link').symlink_to(d/'real')
   with self.assertRaises(AssertionError):versions.arquivo_logico(str((d/'link').relative_to(R)))
if __name__=='__main__':unittest.main(verbosity=2)
