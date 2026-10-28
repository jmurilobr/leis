from pathlib import Path
import importlib.util,tempfile,unittest
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('recuperar53480.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Atomicidade(unittest.TestCase):
 def test_criacao_exclusiva(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';r.durable_new(p,b'original')
   with self.assertRaises(FileExistsError):r.durable_new(p,b'outro')
   self.assertEqual(p.read_bytes(),b'original')
 def test_preimagem_errada(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';p.write_bytes(b'original')
   with self.assertRaises(AssertionError):r.replace_exact(p,b'novo',b'errado')
   self.assertEqual(p.read_bytes(),b'original');self.assertEqual(len(list(Path(d).iterdir())),1)
 def test_troca_exata(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';p.write_bytes(b'original');r.replace_exact(p,b'novo',b'original');self.assertEqual(p.read_bytes(),b'novo');self.assertEqual(len(list(Path(d).iterdir())),1)
 def test_reaplicacao_recusada(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';p.write_bytes(b'original');r.replace_exact(p,b'novo',b'original')
   with self.assertRaises(AssertionError):r.replace_exact(p,b'novo',b'original')
   self.assertEqual(p.read_bytes(),b'novo')
unittest.main()
