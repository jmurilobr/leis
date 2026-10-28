import sys,json,gzip,hashlib,subprocess
from pathlib import Path
from html.parser import HTMLParser
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from preparar_lote_decretos_cache import fields
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
sha=lambda b:hashlib.sha256(b).hexdigest()
class Lists(HTMLParser):
 def __init__(self):super().__init__();self.events=[]
 def handle_starttag(self,t,a):
  if t in ['ol','ul','li']:self.events.append(['inicio',t,sorted((k,z) for k,z in a if k in ['type','start','value'])])
 def handle_endtag(self,t):
  if t in ['ol','ul','li']:self.events.append(['fim',t])
rows=[r for r in json.loads((BASE.parent/'retomada_federal_20261027_002/verificacao_3608.json').read_text())['registros'] if r['path'] in ['federal/decretos/1943/dec-13744-1943-10-26.md','federal/decretos/1943/dec-12418-1943-05-13.md']];assert len(rows)==2
D=BASE/'github_dois';D.mkdir(exist_ok=False);results=[]
proof={}
for name in ['resultado020.json','resultado021_final.json']:
 for r in json.loads((BASE.parent/'retomada_federal_20261027_002'/name).read_bytes())['registros']:proof[r['path']]=r
for i,r in enumerate(rows,1):
 raw=(ROOT/r['arquivo_final']).read_bytes();assert sha(raw)==r['sha256_md_final'];body=fields(raw.decode())[2].lstrip().partition('\n')[2];p=D/f'{i:02}_request.json';p.write_text(json.dumps({'text':body,'mode':'gfm'},ensure_ascii=False)+'\n');response=D/f'{i:02}_response.html';err=D/f'{i:02}_stderr.txt';cmd=['gh','api','--method','POST','markdown','--input',str(p)]
 with response.open('wb') as stdout,err.open('wb') as stderr:run=subprocess.run(cmd,cwd=ROOT,stdout=stdout,stderr=stderr)
 assert run.returncode==0,(r['path'],err.read_text());render=response.read_text();assert '<p' in render or '<div' in render
 source=gzip.decompress((ROOT/r['fonte_html_cache']).read_bytes()).decode();norm=source
 for c in sorted(proof[r['path']]['administrativos_excluidos'],key=lambda c:c['inicio'],reverse=True):assert source[c['inicio']:c['fim']]==c['paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
 a=v.texto_visivel_html(norm);b=v.texto_visivel_html(render);sp=Lists();sp.feed(norm);mp=Lists();mp.feed(render);ok=a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and sp.events==mp.events
 results.append(dict(r,request={'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())},response={'path':str(response.relative_to(ROOT)),'sha256':sha(response.read_bytes())},texto_pontuacao_numeros_contextos_iguais=a==b,estrutura_listas_type_start_value_igual=sp.events==mp.events,listas_fonte=sp.events,listas_render=mp.events,sha256_visivel_fonte=sha(a.encode()),sha256_visivel_github=sha(b.encode()),aprovado=ok));print('GitHub',i,r['path'],'aprovado',ok,flush=True)
res={'escopo':'Exatamente dois POST ao endpoint oficial GitHub markdown para render, sem publicação nem requisição governamental adicional. Requests e responses integrais preservados.','limite':'GitHub pode sanitizar CSS/classes; compara texto, sinais, números/contextos e ol/ul/li/type/start/value. Não afirma identidade visual de CSS.','resumo':{'chamadas':2,'aprovados':sum(r['aprovado'] for r in results),'divergencias':sum(not r['aprovado'] for r in results)},'registros':results};(D/'resultado.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');assert all(r['aprovado'] for r in results)
