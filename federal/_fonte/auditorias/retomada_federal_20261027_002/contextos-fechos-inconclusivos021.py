import json,gzip,re,sys,unicodedata
from pathlib import Path
sys.path.insert(0,'scripts');from estados.pe_fidelidade_visivel import texto_visivel_html
months='janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split();rx=re.compile(r'(?i)\b(?:Rio\s*de\s*Janeiro|Brasilia|Capital\s*Federal),?\s*(?:em\s*)?(\d{1,2})(?:[º°o])?\s*de\s*([a-z]+)\s*de\s*(\d{4,8})(?!\d)');out=[]
for no in [21]:
 for r in json.load(open(f'federal/_lote_dec_continuacao_20261020_{no:03}.json'))['publicaveis']:
  p=Path(r['path'].replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz'));s=texto_visivel_html(gzip.decompress(p.read_bytes()).decode());s=re.split(r'###DEC-[^@]+@@@RET\d+\+{3}',s)[0];n=''.join(c for c in unicodedata.normalize('NFD',s) if not unicodedata.combining(c));ms=[m for m in rx.finditer(n) if m[2].lower() in months]
  if ms:continue
  sig=re.search(r'(?i)juscelino\s+kubi|caf[eé]\s+filho|Ner[eê]u\s+Ramos|Carlos\s+Luz|Get[uú]lio\s+Vargas',s);ctx=s[max(0,sig.start()-190):sig.end()+70] if sig else s[-350:];out.append({'path':r['path'],'data_epigrafe':r['epigrafe']['data'],'contexto':ctx,'assinatura_presidencial_localizada':bool(sig)})
Path('federal/_fonte/auditorias/retomada_federal_20261027_002/contextos-fechos-inconclusivos021.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('TOTAL',len(out))
for r in out:print(r['path'],repr(r['contexto']))
