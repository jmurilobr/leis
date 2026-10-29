"""Executa replay congelado com bloqueio de leitura das raízes privadas e municipais."""
from pathlib import Path
import io,builtins,runpy,os
R=Path(__file__).resolve().parents[4]
original=builtins.open;ioriginal=io.open
forbidden=[R/'_fonte',R/'municipais']
def check(path,mode):
 if isinstance(path,int):return  # Pipes do subprocesso GFM; não são caminhos de arquivos.
 if isinstance(path,(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(path)).resolve()
  assert not any(p==q or q in p.parents for q in forbidden),('Leitura proibida',str(p))
 if isinstance(mode,str):assert not any(x in mode for x in 'wax+'),('Escrita proibida',str(path))
def checked(path,mode='r',*args,**kwargs):check(path,mode);return original(path,mode,*args,**kwargs)
def ichecked(path,mode='r',*args,**kwargs):check(path,mode);return ioriginal(path,mode,*args,**kwargs)
builtins.open=checked;io.open=ichecked
runpy.run_path(str(R/'reguladores/_fonte/auditorias/dou2017_selecao3059_20261028_001/replay3059.py'),run_name='__main__')
