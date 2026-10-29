import ast,os,unittest
from pathlib import Path
B=Path(__file__).resolve().parent
R=B.parents[3]
tree=ast.parse((B/'replay_sem_privados.py').read_text())
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='check')
env={'Path':Path,'os':os,'forbidden':[R/'_fonte',R/'municipais']}
exec(compile(ast.Module(body=[node],type_ignores=[]),'<gate>','exec'),env)
check=env['check']
class Gate(unittest.TestCase):
 def test_private_read(self):
  with self.assertRaises(AssertionError):check(R/'_fonte/test.json','rb')
 def test_municipal_read(self):
  with self.assertRaises(AssertionError):check(R/'municipais/test.md','r')
 def test_file_write(self):
  with self.assertRaises(AssertionError):check(R/'reguladores/test.json','wb')
 def test_public_read(self):check(B/'verificar_publico.py','rb')
 def test_pipe_subprocess(self):check(4,'wb')
if __name__=='__main__':unittest.main()
