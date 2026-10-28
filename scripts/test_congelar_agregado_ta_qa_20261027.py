"""Controles reais: não congelar prova de outro lote ou SHA divergente."""
from pathlib import Path
import json,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import congelar_agregado_ta_qa_20261027 as q
B=q.R/'municipais/_indice/_recuperacao_20261027'

class FreezeQA(unittest.TestCase):
 def invoke(self,directory,replay=None,confronto=None):
  cmd=['freeze','--manifesto',str(B/'agregado586-sucessor-final/entrega-final.json'),'--baseline',str(B/'baseline-head-ta0018/manifesto.json'),'--replay',str(replay or B/'agregado586-replay-integral.json'),'--confronto',str(confronto or B/'agregado586-confronto-conjunto.json'),'--saida',str(Path(directory)/'output')]
  with patch.object(sys,'argv',cmd):q.main()
 def test_real_full_receipt(self):
  with tempfile.TemporaryDirectory(dir=B) as directory:
   self.invoke(directory);m=json.loads((Path(directory)/'output/entrega-final.json').read_text());self.assertEqual(m['normas'],586)
   f=json.loads((Path(directory)/'output/fixtures-head.json').read_text());self.assertEqual(len(f),3);self.assertTrue(all(x['contagem_nova']==0 for x in f))
 def test_wrong_replay_count(self):
  with tempfile.TemporaryDirectory(dir=B) as directory:
   x=q.load(B/'agregado586-replay-integral.json');x['replay_aprovados']-=1;p=Path(directory)/'bad.json';p.write_text(json.dumps(x))
   with self.assertRaises(AssertionError):self.invoke(directory,replay=p)
   self.assertFalse((Path(directory)/'output').exists())
 def test_candidate_changed_since_comparison(self):
  with tempfile.TemporaryDirectory(dir=B) as directory:
   x=q.load(B/'agregado586-confronto-conjunto.json');p0=next(iter(x['sha256_candidatos']));x['sha256_candidatos'][p0]='0'*64;p=Path(directory)/'bad.json';p.write_text(json.dumps(x))
   with self.assertRaises(AssertionError):self.invoke(directory,confronto=p)
   self.assertFalse((Path(directory)/'output').exists())
 def test_collision_is_not_ignored(self):
  with tempfile.TemporaryDirectory(dir=B) as directory:
   x=q.load(B/'agregado586-confronto-conjunto.json');x['colisoes']=[{'caso':'fixture de colisão'}];p=Path(directory)/'bad.json';p.write_text(json.dumps(x))
   with self.assertRaises(AssertionError):self.invoke(directory,confronto=p)
   self.assertFalse((Path(directory)/'output').exists())

if __name__=='__main__':unittest.main()
