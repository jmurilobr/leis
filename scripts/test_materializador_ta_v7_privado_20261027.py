"""Integração real em raiz temporária: fecho, captura e criação exclusiva."""
from pathlib import Path
import importlib.util,json,hashlib,shutil,sys,tempfile,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts')]
import materializar_textos_articulados_sapl_v7_privado_20261027 as material
import auditar_textos_articulados_sapl_v4 as gate
from auditar_municipal import metadados
BASE=R/'municipais/_indice/_recuperacao_20261027'
MAP=BASE/'buritis8-tachados-reparo-privado-20261027/mapa-candidato.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()

class MaterialV7(unittest.TestCase):
 def fixture(self,root):
  data=json.loads(MAP.read_text());original=data['materializacao_original']['registro'];host=original['host'];gatepath=BASE/'lotes/ta-gates-0015';candidate=next(r for r in map(json.loads,(gatepath/'resultados.jsonl').read_text().splitlines()) if r['ta_id']==original['ta_id'] and r['host']==host)
  def copy(path):
   path=Path(path);assert not path.is_absolute();target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((R/path).read_bytes())
  for key in ['prova_frontend','prova_norma','prova_ta','prova_casa']:
   pr=original[key];p=Path(pr['arquivo']);copy(p);copy(pr.get('metadata') or p.with_suffix('.meta.json'))
  copy(original['transcricao']);copy('municipais/_indice/ibge-municipios.json')
  folder=root/'gates';folder.mkdir();proofs=[]
  for suffix in ['tipos','anexos']:
   src=gatepath/(host+'.'+suffix+'.json');target=folder/src.name;target.write_bytes(src.read_bytes());proofs.append(dict(arquivo=str(target.relative_to(root)),sha256=sha(target.read_bytes())))
  annex=json.loads((folder/(host+'.anexos.json')).read_text())
  for pr in annex['evidencias']:
   p=Path(pr['arquivo']);copy(p);copy(pr.get('metadata') or p.with_suffix('.meta.json'))
  (folder/'manifesto.json').write_text(json.dumps(dict(fontes=proofs)));(folder/'resultados.jsonl').write_text(json.dumps(candidate,ensure_ascii=False)+'\n')
  return data,candidate,folder
 def invoke(self,root,folder,out):
  with patch.object(material,'ROOT',root),patch.object(gate,'ROOT',root),patch.object(sys,'argv',['material','--gates',str(folder),'--saida',str(out),'--referencia','2026-10-27']):material.main()
 def test_real_cria_com_tachados_e_nao_sobrescreve(self):
  with tempfile.TemporaryDirectory(dir=BASE) as directory:
   root=Path(directory);data,candidate,folder=self.fixture(root);real_target=R/data['path'];actual_before=real_target.read_bytes() if real_target.exists() else None;self.invoke(root,folder,root/'out1')
   rows=list(map(json.loads,(root/'out1/resultados.jsonl').read_text().splitlines()));self.assertEqual(len(rows),1);self.assertTrue(rows[0]['aprovado'],rows)
   target=root/rows[0]['path'];before=target.read_bytes();text=before.decode();self.assertIn('~~Sebastião Alves~~\n\n~~Secretário~~\n\nSecretário Substituto',text);self.assertNotIn('Nota editorial',text)
   meta=metadados(text);self.assertEqual(meta['capturado_em_fonte'],candidate['prova_frontend']['capturado_em']);self.assertEqual(meta['baixado_em'],'2026-10-27');self.assertTrue(rows[0]['gates']['prova_tachados_preservados']['marcacao_tachado_por_caractere_confere'])
   self.invoke(root,folder,root/'out2');self.assertEqual(json.loads((root/'out2/manifesto.json').read_text())['normas'],0);self.assertEqual(target.read_bytes(),before);self.assertEqual(real_target.read_bytes() if real_target.exists() else None,actual_before)
 def test_data_falsa_no_registro_nao_materializa(self):
  with tempfile.TemporaryDirectory(dir=BASE) as directory:
   root=Path(directory);_,candidate,folder=self.fixture(root);candidate['prova_frontend']['capturado_em']='2026-10-26T00:00:00-03:00';(folder/'resultados.jsonl').write_text(json.dumps(candidate,ensure_ascii=False)+'\n');self.invoke(root,folder,root/'out');r=json.loads((root/'out/resultados.jsonl').read_text().splitlines()[0]);self.assertFalse(r['aprovado']);self.assertIn('data real divergem',r['pendencia'])

if __name__=='__main__':unittest.main()
