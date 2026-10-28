"""Testes estritos de bibliografia literal e candidatos privados sem escrita canônica."""
from pathlib import Path
import json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
NOTE='Matéria publicada no Diário Oficial dos Municípios do Estado do Rio de Janeiro no dia 15/09/2026. Edição 4205 A verificação de autenticidade da matéria pode ser feita informando o código identificador no site: https://www.diariomunicipal.com.br/aemerj/'
class Bibliografia(unittest.TestCase):
 def test_modelo_real_com_edicao_e_url_literais(self):
  r=p.classificar(NOTE,'2026-09-15','2026-10-28T10:26:24.930395-03:00');self.assertEqual(r['edicao_atribuida_API'],'4205');self.assertEqual(r['observacao_literal'],NOTE)
 def test_sufixo_de_edicao_e_url_sem_barra_preservados(self):
  note=NOTE.replace('Edição 4205','Edição 4205a').rstrip('/');r=p.classificar(note,'2026-09-15','2026-10-28T13:00:00+00:00');self.assertEqual(r['edicao_atribuida_API'],'4205a');self.assertEqual(r['URL_literal'],note.split('site: ')[1])
 def test_notas_substantivas_e_ambiguas_retidas(self):
  for suffix in [' Retificada.', ' Entra em vigor amanhã.', ' Anexo não reproduzido.', ' Texto parcial.', ' Conflito de redações.', ' Revogada.', ' Errata publicada.', ' Corrigido no compilado.']:
   with self.subTest(suffix=suffix),self.assertRaises(ValueError):p.classificar(NOTE+suffix,'2026-09-15','2026-10-28T10:26:24-03:00')
 def test_outros_textos_nao_sao_toda_bibliografia(self):
  for note in ['Processo Legislativo nº 123/2026.','Publicado em 2026, mas contém texto parcial.','Não substitui o texto publicado no DOE 2199.','Esta lei decorre de projeto de autoria de vereador.','Publicado no Jornal O Paraná, edição 11.345.']:
   with self.subTest(note=note),self.assertRaises(ValueError):p.classificar(note,'2026-09-15','2026-10-28T10:26:24-03:00')
 def test_data_invalida_futura_e_previa_ao_ato_retidas(self):
  for note,date in [(NOTE.replace('15/09/2026','31/02/2026'),'2026-01-01'),(NOTE.replace('15/09/2026','29/10/2026'),'2026-09-15'),(NOTE,'2026-09-16')]:
   with self.subTest(note=note),self.assertRaises(ValueError):p.classificar(note,date,'2026-10-28T10:26:24-03:00')
 def test_html_url_adulterada_e_fuso_ausente_retidos(self):
  for note,stamp in [(NOTE+'\n<script>x</script>','2026-10-28T10:26:24-03:00'),(NOTE.replace('diariomunicipal.com.br','exemplo.invalid'),'2026-10-28T10:26:24-03:00'),(NOTE,'2026-10-28T10:26:24')]:
   with self.subTest(note=note),self.assertRaises(ValueError):p.classificar(note,'2026-09-15',stamp)
 def test_apenas_tres_campos_acrescentados_corpo_e_h1_iguais(self):
  old=b'---\ntitulo: "Lei"\nsha256_texto: "a"\n---\n\n# Lei\n\nArt. 1\xc2\xba. Texto.  \n';proof=dict(url='https://oficial.leg.br/api/norma/1/',sha256='a'*64);new,added=p.representar(old,NOTE,proof);self.assertEqual(new.replace(added,b'',1),old);self.assertEqual(new.split(b'\n---\n',1)[1],old.split(b'\n---\n',1)[1]);self.assertEqual(p.metadados(new.decode())['observacao_fonte'],NOTE)
 def test_metadado_ja_existente_nao_e_sobrescrito(self):
  old=b'---\nobservacao_fonte: "anterior"\n---\n\n# Lei\n';
  with self.assertRaises(ValueError):p.representar(old,NOTE,dict(url='x',sha256='a'*64))
 def real_row(self,b):
  material=p.q.BASE/'lotes/ta-materializados-0025-v7/resultados.jsonl';r=next(r for r in map(json.loads,material.read_text().splitlines()) if r.get('path','').endswith('decretos-873-2026-sapl-2684.md'));old=p.q.safe(r['path']).read_bytes();note=json.loads(p.q.safe(r['prova_norma']['arquivo']).read_text())['observacao']
  if p.q.sha(old)!=r['sha256']:
   fields=dict(observacao_fonte=note,fonte_metadados=r['prova_norma']['url'],sha256_metadados_fonte=r['prova_norma']['sha256']);added=('\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())).encode();old=old.replace(added,b'',1)
  assert p.q.sha(old)==r['sha256'];new,_=p.representar(old,note,r['prova_norma']);(b/'old.txt').write_bytes(old);(b/'new.txt').write_bytes(new)
  return dict(path=r['path'],preimagem=str((b/'old.txt').relative_to(ROOT)),candidato=str((b/'new.txt').relative_to(ROOT)),sha256_preimagem=p.q.sha(old),sha256_candidato=p.q.sha(new),materializacao=str(material.relative_to(ROOT)),sha256_materializacao=p.q.sha(material.read_bytes()))
 def test_caso_real_API_M_V3_CSS_identidade_e_matrizes(self):
  with tempfile.TemporaryDirectory(dir=p.q.BASE) as tmp:
   row=self.real_row(Path(tmp));proof=p.validar_candidato(row,require_current=False);self.assertTrue(proof['aprovado']);self.assertTrue(proof['corpo_H1_identidade_datas_captura_iguais']);self.assertEqual(proof['API_status'],200)
 def test_corpo_adulterado_recusado_mesmo_com_sha_do_arquivo_atualizado(self):
  with tempfile.TemporaryDirectory(dir=p.q.BASE) as tmp:
   row=self.real_row(Path(tmp));candidate=p.q.safe(row['candidato']);candidate.write_bytes(candidate.read_bytes()+b'Texto extra.\n');row['sha256_candidato']=p.q.sha(candidate.read_bytes())
   with self.assertRaisesRegex(ValueError,'três campos'):p.validar_candidato(row,require_current=False)
if __name__=='__main__':unittest.main()
