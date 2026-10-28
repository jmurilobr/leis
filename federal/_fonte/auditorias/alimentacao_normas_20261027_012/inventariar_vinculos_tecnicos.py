"""Inventário técnico offline antes do fecho; candidatos, nunca máscaras."""
from pathlib import Path
import json,gzip,re,sys,hashlib
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'scripts'))
import baixar_federal as f
from identidade_decreto_revisao import normal
out=[]
current=re.compile(r'\bCOM\s+(?:ESTE|O PRESENTE)(?:[\s,;:–-]+DECRETO)?[\s,;:–-]+BAIXA[M]?\b|\bACOMPANHA[M]?[\s,;:–-]+(?:ESTE|O PRESENTE)[\s,;:–-]+DECRETO\b|\bQUE\s+A\s+ESTE\s+(?:DECRETO\s+)?ACOMPANHA[M]?\b')
objects=re.compile(r'\b(?:PROJETOS?|PROJECTOS?|ORCAMENTOS?|PLANTAS?|PLANOS?|ESTUDOS|PERFIL|PERFIS|ESPECIFICACOES|DESENHOS?)\b')
for r in json.loads((B/'qa_final_v4/preparo.json').read_bytes())['registros']:
 raw=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());assert hashlib.sha256(raw).hexdigest()==r['sha256_html'];blocks=f.convert(raw.decode()).split('\n\n');close=next((i for i,x in enumerate(blocks) if re.match(r'^(?:RIO DE JANEIRO|BRASILIA|CAPITAL FEDERAL)[,.;\s]+(?:EM\s*)?\d',normal(x))),len(blocks));hits=[]
 for i,x in enumerate(blocks[:close]):
  n=normal(x)
  if current.search(n) and objects.search(n):hits.append({'bloco_indice':i,'literal_integral':x,'remissao_match':current.search(n)[0],'objetos_match':objects.findall(n)})
 if hits:out.append({'path':r['path'],'sha256_HTML':r['sha256_html'],'sha256_MD_preliminar':r['sha256_candidato'],'blocos':hits,'fecho':blocks[close] if close<len(blocks) else None,'apos_fecho':'\n\n'.join(blocks[close+1:]),'limites':'Vínculo no mesmo bloco é candidato contextual; tabelas/regulamentos presentes ou remissões históricas exigem leitura, sem retenção automática.'})
p=B/'vinculos_tecnicos.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Vínculos para leitura individual:',len(out));print([r['path'] for r in out])
