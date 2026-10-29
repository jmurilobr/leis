"""Proteções de caminho, identidade e criação sem sobrescrita; sem canônicos."""
from pathlib import Path
import ast,unittest,os,re,shutil
B=Path(__file__).resolve().parent;ROOT=B.parents[3].resolve();tree=ast.parse((B/'promover572.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'safe','key','syncdir','durable'}];assert len(defs)==4
ns={'Path':Path,'ROOT':ROOT,'os':os,'re':re};exec(compile(ast.Module(body=defs,type_ignores=[]),'funcoes_congeladas145','exec'),ns)
class Protecoes(unittest.TestCase):
 def test_caminho_absoluto_recusado(self):
  with self.assertRaises(AssertionError):ns['safe']('/tmp/fora.md')
 def test_travessia_recusada(self):
  with self.assertRaises(AssertionError):ns['safe']('federal/../fora.md')
 def test_alias_numero_colide(self):self.assertEqual(ns['key']('06.107'),ns['key']('6107'))
 def test_hardlink_nao_sobrescreve(self):
  d=B/'teste_criacao_privado';d.mkdir(exist_ok=False)
  try:
   ns['durable'](d/'origem',b'candidato');ns['durable'](d/'destino',b'preimagem')
   with self.assertRaises(FileExistsError):os.link(d/'origem',d/'destino')
   self.assertEqual((d/'destino').read_bytes(),b'preimagem')
  finally:shutil.rmtree(d)
 def test_durable_nao_sobrescreve(self):
  p=B/'teste_durable_privado';ns['durable'](p,b'original')
  try:
   with self.assertRaises(FileExistsError):ns['durable'](p,b'novo')
   self.assertEqual(p.read_bytes(),b'original')
  finally:p.unlink()
if __name__=='__main__':unittest.main(verbosity=2)
