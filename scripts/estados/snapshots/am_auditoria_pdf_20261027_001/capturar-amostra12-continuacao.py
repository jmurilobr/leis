import sys,json,gzip,hashlib,datetime,time,subprocess
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path[:0]=['scripts/estados'];from coletar_rn_fontes import capturar
sha=lambda b:hashlib.sha256(b).hexdigest();base=Path('estaduais/AM/_fonte/auditorias/amostra12-continuacao-20261027-001');base.mkdir(exist_ok=False);rows=[]
for ed,pg in [('588',2),('17515',5),('17515',6)]:
 time.sleep(1.2);url=f'https://diario.imprensaoficial.am.gov.br/apifront/portal/edicoes/pdf_diario/{ed}/{pg}';st,b,h,end=capturar(url);p=base/f'{ed}-{pg}.pdf';p.write_bytes(b);row=dict(edicao_id=ed,pagina=pg,url=url,url_final=end,http=st,PDF=b.startswith(b'%PDF-'),arquivo=str(p),sha256=sha(b),headers={k:v for k,v in h.items() if k.lower() not in ('set-cookie','cookie','authorization','proxy-authorization')},capturado_em=datetime.datetime.now(ZoneInfo('America/Recife')).isoformat());rows.append(row)
 if st in (401,403,429) or st>=500:break
 if st==200 and row['PDF']:subprocess.run(['/opt/homebrew/bin/pdftoppm','-png','-singlefile','-scale-to','3600',str(p),str(p.with_suffix(''))],check=True);subprocess.run(['/opt/homebrew/bin/pdftotext',str(p),str(p.with_suffix('.txt'))],check=True)
 print(ed,pg,st,flush=True)
Path('scripts/estados/manifestos/am-amostra12-continuacao-20261027-001.json').write_text(json.dumps(dict(capturas=rows,origem_paginas='índices oficiais capturados em am-amostra12-PDF-capturas-20261027-001.json; API PDF observada no JS oficial',omissao_headers_sessao=True),ensure_ascii=False,indent=2)+'\n')
