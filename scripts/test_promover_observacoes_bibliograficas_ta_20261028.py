"""Default dry-run e atomicidade isolada do promotor bibliográfico ROOT-only."""
from pathlib import Path
import os,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_observacoes_bibliograficas_ta_20261028 as p
class Promotor(unittest.TestCase):
 def rows(self,b):
  rows=[]
  for i in range(2):
   old=('anterior '+str(i)).encode();new=('candidato '+str(i)).encode();t=b/f'{i}.md';t.write_bytes(old);s=b/f'{i}.txt';s.write_bytes(new);rows.append(dict(path=str(t),preparado=str(s),sha256_preimagem=p.p.q.sha(old),sha256_candidato=p.p.q.sha(new)))
  return rows
 def test_dry_run_por_padrao_apply_so_explicito(self):
  args=['--manifesto','m.json','--sha256','a'*64,'--saida','nova'];self.assertFalse(p.argumentos().parse_args(args).apply);self.assertTrue(p.argumentos().parse_args(args+['--apply']).apply)
 def test_copia_backup_exclusivo_e_troca_isolada(self):
  with tempfile.TemporaryDirectory(dir=p.p.q.BASE) as tmp:
   b=Path(tmp);rows=self.rows(b);r=p.p.q.aplicar_transacao(rows,b/'backup',resolve=Path);self.assertEqual(len(r['aplicados']),2);self.assertEqual((b/'backup/0.txt').read_bytes(),b'anterior 0');self.assertEqual((b/'0.md').read_bytes(),b'candidato 0')
   with self.assertRaises(FileExistsError):p.p.q.aplicar_transacao(rows,b/'backup',resolve=Path)
 def test_preimagem_divergente_nao_troca_nenhum(self):
  with tempfile.TemporaryDirectory(dir=p.p.q.BASE) as tmp:
   b=Path(tmp);rows=self.rows(b);rows[1]['sha256_preimagem']='0'*64
   with self.assertRaises(ValueError):p.p.q.aplicar_transacao(rows,b/'backup',resolve=Path)
   self.assertEqual((b/'0.md').read_bytes(),b'anterior 0');self.assertEqual((b/'1.md').read_bytes(),b'anterior 1')
 def test_rollback_conservador_apos_falha_da_segunda_troca(self):
  with tempfile.TemporaryDirectory(dir=p.p.q.BASE) as tmp:
   b=Path(tmp);rows=self.rows(b);calls=[]
   def fail(a,z):
    calls.append(z)
    if len(calls)==2:raise OSError('falha simulada')
    os.replace(a,z)
   with self.assertRaises(OSError):p.p.q.aplicar_transacao(rows,b/'backup',resolve=Path,replace=fail)
   self.assertEqual((b/'0.md').read_bytes(),b'anterior 0');self.assertEqual((b/'1.md').read_bytes(),b'anterior 1')
if __name__=='__main__':unittest.main()
