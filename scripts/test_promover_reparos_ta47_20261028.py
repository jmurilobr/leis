"""Provas reais V3 e transações isoladas; nunca aplica em canônicos do acervo."""
from pathlib import Path
import json,os,stat,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as p

def originais():
 rows=[dict(r,modo='escapes') for r in json.loads((p.BASE/'reparos-escapes-ta-46-privado-20261027/mapa-candidatos.json').read_text())['candidatos']]
 return rows+[dict(json.loads((p.BASE/'buritis8-tachados-reparo-privado-v2-20261027/mapa-candidato.json').read_text()),modo='tachados')]

class Promocao47(unittest.TestCase):
 def fixtures(self,b):
  rows=[]
  for i in range(2):
   old=('preimagem '+str(i)).encode();new=('candidato '+str(i)).encode();target=b/(str(i)+'.md');target.write_bytes(old);target.chmod(0o640);prep=b/(str(i)+'.txt');prep.write_bytes(new)
   rows.append(dict(path=str(target),preparado=str(prep),sha256_preimagem=p.sha(old),sha256_candidato=p.sha(new)))
  return rows
 def test_transacao_atomica_backups_e_permissoes(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);r=p.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual(len(r['aplicados']),2)
   for i,row in enumerate(rows):
    self.assertEqual(p.sha(Path(row['path']).read_bytes()),row['sha256_candidato']);self.assertEqual(p.sha((b/'backup'/f'{i}.txt').read_bytes()),row['sha256_preimagem']);self.assertEqual(stat.S_IMODE(Path(row['path']).stat().st_mode),0o640)
 def test_segunda_preimagem_invalida_impede_todas_trocas(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);rows[1]['sha256_preimagem']='0'*64
   with self.assertRaisesRegex(ValueError,'Preimagem/preparado'):p.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual(Path(rows[0]['path']).read_bytes(),b'preimagem 0');self.assertEqual(Path(rows[1]['path']).read_bytes(),b'preimagem 1')
 def test_falha_segunda_troca_reverte_primeira(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);calls=[]
   def fail_second(a,z):
    calls.append(z)
    if len(calls)==2:raise OSError('falha simulada')
    os.replace(a,z)
   with self.assertRaisesRegex(OSError,'simulada'):p.aplicar_transacao(rows,b/'backup',resolve=Path,replace=fail_second)
   self.assertEqual(Path(rows[0]['path']).read_bytes(),b'preimagem 0');self.assertEqual(Path(rows[1]['path']).read_bytes(),b'preimagem 1');r=json.loads((b/'backup/transacao.json').read_text());self.assertEqual(r['revertidos'],[rows[0]['path']]);self.assertFalse(r['erros_rollback'])
 def test_symlink_recusado_sem_troca(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);link=b/'link.md';link.symlink_to(rows[0]['path']);rows[0]['path']=str(link)
   with self.assertRaises(ValueError):p.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual((b/'0.md').read_bytes(),b'preimagem 0')
 def test_backup_existente_nao_sobrescreve(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);(b/'backup').mkdir();(b/'backup/prova').write_text('preservar')
   with self.assertRaises(FileExistsError):p.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual((b/'0.md').read_bytes(),b'preimagem 0');self.assertEqual((b/'backup/prova').read_text(),'preservar')
 def test_candidato_alterado_impede_trocas(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);rows=self.fixtures(b);Path(rows[1]['preparado']).write_bytes(b'divergente')
   with self.assertRaises(ValueError):p.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual((b/'0.md').read_bytes(),b'preimagem 0')
 def test_exportacao_isolada_preserva_canonicose_hashes(self):
  rows=originais();before={r['path']:p.sha(p.safe(r['path']).read_bytes()) for r in rows}
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   out=p.exportar(rows,Path(tmp)/'exportados');self.assertEqual(len(out),47)
   for r in out:self.assertEqual(p.sha(p.safe(r['preparado']).read_bytes()),r['sha256_candidato'])
   for r in rows:self.assertEqual(p.sha(p.safe(r['path']).read_bytes()),before[r['path']])
   with self.assertRaises(FileExistsError):p.exportar(rows,Path(tmp)/'exportados')
 def test_manifesto_rejeita_mutacao(self):
  with tempfile.TemporaryDirectory(dir=p.BASE) as tmp:
   b=Path(tmp);f=b/'evidencia';f.write_bytes(b'original');m=b/'m.json';m.write_text(json.dumps(dict(arquivos=[p.info(f)])));digest=p.sha(m.read_bytes());p.verificar_manifesto(m,digest);f.write_bytes(b'mudou')
   with self.assertRaises(ValueError):p.verificar_manifesto(m,digest)
 def test_47_casos_reais_fulltext_strike_contexto_numeros_matrizes(self):
  names=[r['nome'] for r in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text())]
  for row in originais():
   with self.subTest(path=row['path']):
    _,_,proof=p.validar_linha(row,names);self.assertTrue(proof['replay']['aprovado']);self.assertTrue(proof['replay']['marcacao_tachado_por_caractere_confere']);self.assertTrue(proof['replay']['atributos_contextuais_tachados_conferem'])
 def test_buritis_perda_markup_mesmo_texto_nao_passa(self):
  row=originais()[-1];raw=p.safe(row['candidato']).read_text();body=p.corpo(raw).replace('~~','');source=p.safe(row['fonte']['arquivo']).read_text();proof=p.comparar(source,body);self.assertFalse(proof['aprovado']);self.assertTrue(proof['igualdade_caracteres_nao_brancos']);self.assertFalse(proof['marcacao_tachado_por_caractere_confere'])
if __name__=='__main__':unittest.main()
