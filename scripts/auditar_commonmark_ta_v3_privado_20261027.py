"""Replay privado completo: texto, números e máscara do tachado por caractere."""
from pathlib import Path
import argparse,hashlib,json,sys
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'scripts'))
from perfil_ta_tachados_preservados_20261027 import comparar
from comum import decodificar

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ['lista','materializados','saida']:ap.add_argument('--'+key,type=Path,required=True)
 a=ap.parse_args();material={r.get('path'):r for r in map(json.loads,(a.materializados/'resultados.jsonl').read_text().splitlines()) if r.get('aprovado')};rows=[]
 for path in a.lista.read_text().splitlines():
  r=dict(path=path,aprovado=False)
  try:
   m=material[path];raw=(R/path).read_bytes();s=m['prova_frontend'];source=(R/s['arquivo']).read_bytes();assert sha(raw)==m['sha256'] and sha(source)==s['sha256']
   body=raw.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1];r.update(comparar(decodificar(source,s['content_type']),body));r.update(sha256=sha(raw),fonte=s)
  except Exception as error:r['erro']=type(error).__name__+': '+str(error)
  rows.append(r)
 a.saida.mkdir(exist_ok=False,parents=True)
 for name,state in [('aprovados',True),('retidos',False)]: (a.saida/(name+'.paths.txt')).write_text(''.join(r['path']+'\n' for r in rows if r['aprovado']==state))
 result=dict(arquivos=len(rows),aprovados=sum(r['aprovado'] for r in rows),retidos=sum(not r['aprovado'] for r in rows),resultados=rows,codigo_sha256=sha(Path(__file__).read_bytes()),criterio='Todos os caracteres não brancos, números e marcação de tachado nas mesmas posições; nenhuma classificação jurídica de trechos tachados.')
 (a.saida/'controle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['arquivos','aprovados','retidos']}))

if __name__=='__main__':main()
