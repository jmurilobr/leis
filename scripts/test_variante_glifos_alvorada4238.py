import hashlib,json,re,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preparar_variante_glifos_alvorada4238 import preparar
from preparar_reparo_alvorada4238_v2 import preparar as anterior,conferir_replay
class TestGlifos(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.candidate,cls.native,cls.proof=preparar()
 def test_so_dois_sinais_e_hash(self):
  old,_,_=anterior();normalize=lambda t:re.sub(r'(?m)^sha256_texto:.*$','sha256_texto: HASH',t)
  self.assertEqual(normalize(self.candidate),normalize(old).replace('\u2015','\u201c').replace('\u2016','\u201d'));self.assertEqual(len(self.proof['alteracoes_corpo']),2);self.assertIn('2-Aº',self.candidate)
 def test_fonte_comprova_glifos(self):
  for table in self.proof['cmap_fonte']:
   self.assertEqual(table['mapeamento']['U+201C'],179);self.assertEqual(table['mapeamento']['U+201D'],180);self.assertEqual(table['mapeamento']['U+2015'],0);self.assertEqual(table['mapeamento']['U+2016'],0)
 def test_replay_integral(self):
  body=self.candidate.split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1][:-1];self.assertTrue(conferir_replay(body,self.native));self.assertEqual(len(''.join(self.native.split())),2498)
if __name__=='__main__':unittest.main()
