import json,gzip,sys,re,unicodedata,datetime
from pathlib import Path
sys.path.insert(0,'scripts');from estados.pe_fidelidade_visivel import texto_visivel_html
months={m:i for i,m in enumerate(['janeiro','fevereiro','marco','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'],1)};out=[];counts={};allrows=[]
for no in [21]:
 p=Path(f'federal/_lote_dec_continuacao_20261020_{no:03}.json');rows=json.load(open(p))['publicaveis'];cnt={'total':len(rows),'sem_fecho_reconhecido':0,'ultimo_fecho_concordante':0,'ultimo_fecho_divergente':0}
 for r in rows:
  sp=Path(r['path'].replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz'));source=gzip.decompress(sp.read_bytes()).decode();text=texto_visivel_html(source);text=re.split(r'###DEC-[^@]+@@@RET\d+\+{3}',text)[0];norm=''.join(c for c in unicodedata.normalize('NFD',text) if not unicodedata.combining(c));matches=[]
  for m in re.finditer(r'(?i)\b(?:Rio\s*de\s*Janeiro|Brasilia|Capital\s*Federal),?\s*(?:em\s*)?(\d{1,2})(?:[º°o])?\s*de\s*([a-z]+)\s*de\s*(\d{4,8})(?!\d)',norm):
   day,month,year=m.groups()
   if month.lower() not in months:continue
   try:date=datetime.date(int(year),months[month.lower()],int(day)).isoformat()
   except ValueError:date=None
   matches.append({'data':date,'literal':text[m.start():m.end()],'contexto':text[max(0,m.start()-100):m.end()+200]})
  if not matches:cnt['sem_fecho_reconhecido']+=1;continue
  if matches[-1]['data']==r['epigrafe']['data']:cnt['ultimo_fecho_concordante']+=1
  else:cnt['ultimo_fecho_divergente']+=1;out.append({'lote':no,'path':r['path'],'urn':r['urn'],'sha256_md':r['sha256'],'sha256_fonte_html':r['sha256_fonte_html'],'epigrafe':r['epigrafe'],'fechos':matches})
 counts[no]=cnt
Path('federal/_fonte/auditorias/retomada_federal_20261027_002/triagem-fechos021-v1.json').write_text(json.dumps({'contagens':counts,'divergencias':out},ensure_ascii=False,indent=2)+'\n');print(json.dumps(counts,ensure_ascii=False),flush=True)
for r in out:print(r['path'],r['fechos'][-1]['literal'],flush=True)
