import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import materializar_textos_articulados_sapl_v5 as m
class TestIndiceMaterializacao(unittest.TestCase):
 def cache(self,folder,name,records,status=200):
  raw=json.dumps({'results':records}).encode() if status==200 else b'';p=folder/(name+'.json');p.write_bytes(raw);p.with_suffix('.meta.json').write_text(json.dumps(dict(url='https://sapl.a.leg.br/api/compilacao/textoarticulado/?page_size=100&page='+name,status=status,sha256=hashlib.sha256(raw).hexdigest())))
 def test_http404_nao_e_prova_e_nao_apaga_registro200(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.cache(root,'1',[{'id':1,'privacidade':0}]);self.cache(root,'61',[],404)
   with patch.object(m,'ROOT',root):records,conflicts,unused=m.carregar_indice(root)
   self.assertEqual(records[1][0]['privacidade'],0);self.assertFalse(conflicts);self.assertEqual(unused[0]['status'],404)
 def test_conflito_publico_privado_retido(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.cache(root,'1',[{'id':1,'privacidade':0}]);self.cache(root,'2',[{'id':1,'privacidade':1}])
   with patch.object(m,'ROOT',root):records,conflicts,_=m.carregar_indice(root)
   self.assertIn(1,conflicts)
 def test_sha_corrompido_nao_ignorado(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.cache(root,'1',[{'id':1}]);(root/'1.json').write_bytes(b'{}')
   with patch.object(m,'ROOT',root):
    with self.assertRaises(ValueError):m.carregar_indice(root)
if __name__=='__main__':unittest.main()
