import sys,json,gzip,hashlib,datetime,time,re,urllib.parse,os
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path[:0]=['scripts/estados'];from coletar_rn_fontes import capturar
SHA=lambda b:hashlib.sha256(b).hexdigest();selection=Path('scripts/estados/manifestos/am-amostra-adicional12-20261027-001.json');sel=json.loads(selection.read_text());base=Path('estaduais/AM/_fonte/auditorias/amostra12-PDF-20261027-001');base.mkdir(exist_ok=False);cache={}
for file in ['am-edicoes-integrais-20261027-001.json','am-amostra-PDF-capturas-20261027-001.json','am-amostra-PDF-capturas-20261027-002.json','am-amostra-PDF-continuacao-20261027-001.json','am-legisla-suplementos-paginas-20261027-001.json']:
 for r in json.loads((Path('scripts/estados/manifestos')/file).read_text())['capturas']:
  if r.get('http')==200:cache[r['url']]=dict(r,receipt_origem='scripts/estados/manifestos/'+file)
rows=[];stopped=False;bad=0
with (base/'capturas.jsonl').open('x') as log:
 for it in sel['selecao']:
  raw=gzip.decompress(Path(it['captura']['cache']).read_bytes());assert SHA(raw)==it['captura']['sha256_fonte'];link=re.search(r'href="(/diario_am/completo/'+it['id_legisla']+')"',raw.decode());queue=[('viewer',urllib.parse.urljoin('https://legisla.imprensaoficial.am.gov.br',link[1]))] if link else []
  if not queue:rows.append(dict(id_legisla=it['id_legisla'],erro='link do diário não observado'));continue
  while queue:
   if not Path('.git').exists():raise ValueError('volume ausente; parar')
   kind,url=queue.pop(0);r=dict(id_legisla=it['id_legisla'],tipo=kind,url=url,iniciado_em=datetime.datetime.now(ZoneInfo('America/Recife')).isoformat())
   if url in cache:
    old=cache[url];z=Path(old['cache']).read_bytes();b=gzip.decompress(z);assert SHA(z)==old['sha256_cache'] and SHA(b)==old['sha256_fonte'];st=200;end=old['url_final'];r.update(http=st,url_final=end,cache=old['cache'],sha256_fonte=old['sha256_fonte'],sha256_cache=old['sha256_cache'],PDF=old.get('PDF',False),reutilizado_de=old.get('receipt_origem','captura anterior do mesmo lote'),capturado_em_original=old.get('capturado_em',old.get('finalizado_em')))
   else:
    time.sleep(1.2)
    try:st,b,h,end=capturar(url)
    except Exception as e:r.update(erro=type(e).__name__+': '+str(e));rows.append(r);log.write(json.dumps(r,ensure_ascii=False)+'\n');log.flush();os.fsync(log.fileno());bad+=1;break
    p=base/(SHA(b)+'.bin.gz')
    if not p.exists():p.write_bytes(gzip.compress(b))
    r.update(http=st,url_final=end,cache=str(p),sha256_fonte=SHA(b),sha256_cache=SHA(p.read_bytes()),PDF=b.startswith(b'%PDF-'),bytes=len(b),headers={k:v for k,v in h.items() if k.lower() not in ('set-cookie','cookie','authorization','proxy-authorization')},finalizado_em=datetime.datetime.now(ZoneInfo('America/Recife')).isoformat());cache[url]=dict(r)
   if kind=='viewer' and st==200:
    u=urllib.parse.urlparse(end);ed=re.search(r'/pdf/(\d+)/',u.path);pg=re.search(r'p:(\d+)',u.fragment)
    if ed and pg and u.netloc=='diario.imprensaoficial.am.gov.br':r.update(edicao_id=ed[1],pagina=int(pg[1]));queue.extend([('indice_paginas','https://diario.imprensaoficial.am.gov.br/apifront/portal/edicoes/edicao_imagens/'+ed[1]),('PDF_pagina','https://diario.imprensaoficial.am.gov.br/apifront/portal/edicoes/pdf_diario/'+ed[1]+'/'+pg[1])])
   rows.append(r);log.write(json.dumps(r,ensure_ascii=False)+'\n');log.flush();os.fsync(log.fileno());print(it['id_legisla'],kind,st,'PDF',r.get('PDF'), 'cache' if 'reutilizado_de' in r else 'HTTP',flush=True)
   bad=bad+1 if st>=500 else 0
   if st in (401,403,429) or bad>=3:stopped=True;break
   if st!=200:break
  if stopped:break
Path('scripts/estados/manifestos/am-amostra12-PDF-capturas-20261027-001.json').write_text(json.dumps(dict(selecao=str(selection),sha256_selecao=SHA(selection.read_bytes()),capturas=rows,parada_conservadora=stopped,sem_MD=True),ensure_ascii=False,indent=2)+'\n')
