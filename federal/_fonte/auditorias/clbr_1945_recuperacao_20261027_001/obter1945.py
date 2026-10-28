"""Uma captura da URL primária observada; sem retry, paralelo só ao host Normas."""
from pathlib import Path
import json,gzip,hashlib,urllib.request,datetime,fcntl,subprocess
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();lock=(B/'biblioteca.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);catalog=ROOT/'federal/_fonte/auditorias/clbr_fontes_20261027_002/decada1941.html.gz';html=gzip.decompress(catalog.read_bytes());url='https://bd.camara.leg.br/bd/bitstreams/603d71d4-ab0c-421a-9a7a-2dd1210c74ca/download';assert url.encode() in html;(B/'catalogo-oficial-arquivado.html.gz').write_bytes(catalog.read_bytes());(B/'catalogo-recibo-anterior.json').write_bytes(catalog.with_name('recibo-decada1941.json').read_bytes());index=ROOT/'federal/_indice/DEC.json';raw=index.read_bytes();docs=json.loads(raw)['ListaDocumento']['documentos']['documento'];matching=[d for d in docs if str(d.get('numero'))=='20175' and d.get('anoassinatura')=='1945'];assert matching;(B/'identidade_indice20175.json').write_text(json.dumps({'indice_path':str(index.relative_to(ROOT)),'sha256_indice_integral':sha(raw),'registros':matching},ensure_ascii=False,indent=2)+'\n');dest=B/'1945-decretos.pdf';receipt=B/'recibo1945.json';assert not dest.exists() and not receipt.exists();part=dest.with_suffix('.pdf.part');assert not part.exists();r={'url_primaria_observada':url,'catalogo_path':str(catalog.relative_to(ROOT)),'sha256_catalogo_raw':sha(html),'captura_inicio_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'retry':0,'origem':'Captura nova única autorizada, nenhuma autoria de cache presumida.'}
try:
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; arquivo-legislativo; consulta-documental)','Accept':'application/pdf'})
 with urllib.request.urlopen(req,timeout=120) as response:
  r.update(status_http=response.status,url_final=response.url,headers=dict(response.headers));assert response.status==200
  digest=hashlib.sha256();length=0
  with part.open('xb') as out:
   while True:
    chunk=response.read(1024*1024)
    if not chunk:break
    if length==0:assert chunk.startswith(b'%PDF'),'Resposta não é PDF; não tentar novamente'
    out.write(chunk);digest.update(chunk);length+=len(chunk)
  r.update(bytes=length,sha256_PDF=digest.hexdigest(),captura_fim_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());assert length>100000;part.rename(dest);r['arquivo']=str(dest.relative_to(ROOT));r['pdfinfo']=subprocess.check_output(['pdfinfo',str(dest)],text=True)
except Exception as e:
 r.update(estado='falha_retida_sem_retry',erro=str(e));receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');raise
r['estado']='PDF primário capturado; identidade de volume/páginas ainda exige inspeção';receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['estado'],r['bytes'],r['sha256_PDF'],flush=True)
