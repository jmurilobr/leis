import argparse,json,hashlib,gzip
from pathlib import Path
from visibilidade_pdf_to import conferir
SHA=lambda b:hashlib.sha256(b).hexdigest()
def replay(entrada,mapa):
 m=json.loads(Path(entrada).read_text());maps=json.loads(Path(mapa).read_text())
 if maps.get(entrada)!=SHA(Path(entrada).read_bytes()):raise ValueError('entrada fora do mapa')
 for p,s in maps.items():
  path=Path(p)
  if path.is_absolute() or '..' in path.parts or SHA(path.read_bytes())!=s:raise ValueError('SHA/caminho divergente '+p)
 for r in m['documentos']:
  cap=r['captura'];z=Path(cap['cache']).read_bytes();raw=gzip.decompress(z)
  if SHA(z)!=cap['sha256_cache'] or SHA(raw)!=cap['sha256_fonte'] or SHA(Path(r['privado']).read_bytes())!=r['sha256_md']:raise ValueError('fonte/candidato diverge')
  if conferir(raw)!=r['visibilidade']:raise ValueError('replay de visibilidade diverge')
 return dict(total=len(m['documentos']),aprovados=len(m['documentos']),falhas=0,rede=False,alterados=0)
def main():
 p=argparse.ArgumentParser();p.add_argument('--entrada',required=True);p.add_argument('--mapa',required=True);p.add_argument('--recibo',required=True);a=p.parse_args();r=replay(a.entrada,a.mapa)
 with Path(a.recibo).open('x') as f:f.write(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r))
if __name__=='__main__':main()
