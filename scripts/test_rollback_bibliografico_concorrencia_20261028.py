"""Rollback recusa sobrescrever edição externa; diretório symlink é recusado."""
from pathlib import Path
import json,os,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_observacoes_bibliograficas_ta_20261028 as p
class Conservador(unittest.TestCase):
 def test_rollback_preserva_alteracao_externa_e_backup(self):
  with tempfile.TemporaryDirectory(dir=p.p.q.BASE) as tmp:
   b=Path(tmp);rows=[]
   for i in range(2):
    old=('anterior '+str(i)).encode();new=('candidato '+str(i)).encode();target=b/f'{i}.md';target.write_bytes(old);prepared=b/f'{i}.txt';prepared.write_bytes(new);rows.append(dict(path=str(target),preparado=str(prepared),sha256_preimagem=p.p.q.sha(old),sha256_candidato=p.p.q.sha(new)))
   calls=[]
   def external_then_fail(a,z):
    calls.append(z)
    if len(calls)==2:
     Path(rows[0]['path']).write_bytes(b'edicao externa a preservar');raise OSError('falha com interferencia externa')
    os.replace(a,z)
   with self.assertRaises(OSError):p.p.q.aplicar_transacao(rows,b/'backup',resolve=Path,replace=external_then_fail)
   self.assertEqual((b/'0.md').read_bytes(),b'edicao externa a preservar');self.assertEqual((b/'1.md').read_bytes(),b'anterior 1');self.assertEqual((b/'backup/0.txt').read_bytes(),b'anterior 0');report=json.loads((b/'backup/transacao.json').read_text());self.assertEqual(len(report['erros_rollback']),1);self.assertFalse(report['revertidos'])
 def test_diretorio_symlink_recusado_em_raiz_isolada(self):
  with tempfile.TemporaryDirectory(dir=p.p.q.BASE) as tmp:
   b=Path(tmp);(b/'municipais/RJ').mkdir(parents=True);(b/'alvo').mkdir();(b/'municipais/RJ/exemplo').symlink_to(b/'alvo',target_is_directory=True)
   with patch.object(p,'ROOT',b),patch.object(p.p.q,'ROOT',b):
    with self.assertRaisesRegex(ValueError,'symlink'):p.destino('municipais/RJ/exemplo/norma.md')
   self.assertFalse((b/'alvo/norma.md').exists())
if __name__=='__main__':unittest.main()
