"""Export fora do final, referências hash-bound e ausência de fallback por nome."""
from pathlib import Path
import json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import revalidar_observacoes_bibliograficas_ta_v2_privado_20261028 as r
class Cadeia(unittest.TestCase):
 def fixture(self,b):
  canonical='municipais/RJ/exemplo/decretos/2026/decreto-1.md';original=b/'original';final=b/'final';original.mkdir();final.mkdir();export=original/'exportados'/canonical;export.parent.mkdir(parents=True);export.write_bytes(b'candidato literal');base=original/'manifesto.json';base.write_text(json.dumps(dict(arquivos=[r.p.q.info(export)])));ref=r.p.q.info(base);root=final/'manifesto.json';root.write_text(json.dumps(dict(arquivos=[ref,r.p.q.info(export)],manifesto_origem=ref)));row=dict(path=canonical,sha256_candidato=r.p.q.sha(export.read_bytes()))
  return root,base,export,row
 def test_resolve_export_na_origem_sem_supor_pasta_final(self):
  with tempfile.TemporaryDirectory(dir=r.p.q.BASE) as tmp:
   root,base,export,row=self.fixture(Path(tmp));nodes=r.carregar_cadeia(root,r.p.q.sha(root.read_bytes()));result=r.resolver_export(row,nodes);self.assertEqual(result['exportacao']['arquivo'],str(export.relative_to(ROOT)));self.assertEqual(len(nodes),2);self.assertFalse((root.parent/'exportados').exists())
 def test_ref_nao_vinculada_ao_pai_e_recusada(self):
  with tempfile.TemporaryDirectory(dir=r.p.q.BASE) as tmp:
   root,base,export,row=self.fixture(Path(tmp));m=json.loads(root.read_text());m['arquivos']=[r.p.q.info(export)];root.write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'não vinculada'):r.carregar_cadeia(root,r.p.q.sha(root.read_bytes()))
 def test_mutacao_export_e_detectada(self):
  with tempfile.TemporaryDirectory(dir=r.p.q.BASE) as tmp:
   root,base,export,row=self.fixture(Path(tmp));digest=r.p.q.sha(root.read_bytes());export.write_bytes(b'modificado')
   with self.assertRaises(ValueError):r.carregar_cadeia(root,digest)
 def test_nao_busca_export_nao_registrado(self):
  with tempfile.TemporaryDirectory(dir=r.p.q.BASE) as tmp:
   root,base,export,row=self.fixture(Path(tmp));base.write_text(json.dumps(dict(arquivos=[])));ref=r.p.q.info(base);root.write_text(json.dumps(dict(arquivos=[ref],manifesto_origem=ref)));nodes=r.carregar_cadeia(root,r.p.q.sha(root.read_bytes()))
   with self.assertRaisesRegex(ValueError,'Nenhuma exportação'):r.resolver_export(row,nodes)
 def test_nome_certo_com_sha_errado_nao_basta(self):
  with tempfile.TemporaryDirectory(dir=r.p.q.BASE) as tmp:
   root,base,export,row=self.fixture(Path(tmp));nodes=r.carregar_cadeia(root,r.p.q.sha(root.read_bytes()));row['sha256_candidato']='0'*64
   with self.assertRaises(ValueError):r.resolver_export(row,nodes)
 def test_cadeia_real_de_quatro_manifestos_e_89_exports(self):
  root=r.p.q.BASE/'promotor-bibliografico89-final-v2-20261028/manifesto.json';nodes=r.carregar_cadeia(root,'52c91cda8ee4f1f5f8945d95412114ea4ed7af15e7b630d7d0582e37fffd8bf4');self.assertEqual(len(nodes),4);rows=json.loads(r.p.q.safe(nodes[0]['manifesto']['mapa_candidatos']).read_text())['candidatos'];self.assertEqual(len(rows),89)
  for row in rows:self.assertEqual(r.resolver_export(row,nodes)['exportacao']['sha256'],row['sha256_candidato'])
if __name__=='__main__':unittest.main()
