"""Complemento autorizado de até 12 renders oficiais, sem publicar conteúdo.

Executar somente depois da confirmação ROOT da integração do guard privado.
"""
import sys,json,hashlib,subprocess,re,time,datetime
from pathlib import Path
from html.parser import HTMLParser
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
from integridade_html_federal import Visivel
sha=lambda b:hashlib.sha256(b).hexdigest()
class Lists(HTMLParser):
 def __init__(self):super().__init__();self.events=[]
 def handle_starttag(self,t,a):
  if t in ['ol','ul','li']:self.events.append(['inicio',t,sorted((k,z) for k,z in a if k in ['type','start','value'])])
 def handle_endtag(self,t):
  if t in ['ol','ul','li']:self.events.append(['fim',t])
class Matrices(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.tables=[];self.stack=[]
 def handle_starttag(self,t,a):
  if t in ['p','div','br','tr','td','th','table']:
   for s in self.stack:
    if s['cell'] is not None:s['cell']['parts'].append(' ')
  if t=='table':
   q={'rows':[],'cell':None};self.tables.append(q);self.stack.append(q)
  elif self.stack and t=='tr':self.stack[-1]['rows'].append([])
  elif self.stack and t in ['td','th']:
   q=self.stack[-1];assert q['rows'];at=dict(a);c={'tag':t,'rowspan':int(at.get('rowspan') or 1),'colspan':int(at.get('colspan') or 1),'parts':[]};assert c['rowspan']>0 and c['colspan']>0;q['rows'][-1].append(c);q['cell']=c
 def handle_endtag(self,t):
  if t in ['p','div','br','tr','td','th','table']:
   for s in self.stack:
    if s['cell'] is not None:s['cell']['parts'].append(' ')
  if t=='table':assert self.stack;self.stack.pop()
  elif self.stack and t in ['td','th']:self.stack[-1]['cell']=None
 def handle_data(self,s):
  for q in self.stack:
   if q['cell'] is not None:q['cell']['parts'].append(s)
 def result(self):
  result=[]
  for t in self.tables:
   grid={};rows=[]
   for y,row in enumerate(t['rows']):
    x=0;out=[]
    for cell in row:
     while (y,x) in grid:x+=1
     c={k:v for k,v in cell.items() if k!='parts'};c['texto']=' '.join(''.join(cell['parts']).split());out.append(c)
     for yy in range(y,y+c['rowspan']):
      for xx in range(x,x+c['colspan']):assert (yy,xx) not in grid;grid[(yy,xx)]={'origem':[y,x],'texto':c['texto'],'tag':c['tag']}
     x+=c['colspan']
    rows.append(out)
   height=max((y for y,x in grid),default=-1)+1;width=max((x for y,x in grid),default=-1)+1;result.append({'celulas_por_linha':rows,'grade_expandida':[[grid.get((y,x)) for x in range(width)] for y in range(height)]})
  return result
assert '--confirmado-root' in sys.argv,'Aguardar integração ROOT e executar com --confirmado-root';sourcepath=BASE/'nativos12_revisao_ROOT.json';rows=[r for r in json.loads(sourcepath.read_text())['registros'] if r['path']!='federal/decretos/1942/dec-8886-1942-03-02.md'];assert len(rows)==11;proof={r['path']:r for r in json.loads((BASE/'resultado.json').read_text())['registros']};D=BASE/'github_onze_restantes';D.mkdir(exist_ok=False);results=[];blocked=False;guardsha=sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes())
for i,r in enumerate(rows,2):
 raw=(ROOT/r['candidato']).read_bytes();assert sha(raw)==r['sha256_candidato'];assert r['md_candidato_utf8'].encode()==raw;body=raw.decode().split('---',2)[2].lstrip().partition('\n')[2];assert len(body.encode())<=400000;p=D/f'{i:02}_request.json';p.write_text(json.dumps({'text':body,'mode':'gfm'},ensure_ascii=False)+'\n');response=D/f'{i:02}_response.html';err=D/f'{i:02}_stderr.txt';time.sleep(.5)
 with response.open('wb') as stdout,err.open('wb') as stderr:run=subprocess.run(['gh','api','--method','POST','markdown','--input',str(p)],cwd=ROOT,stdout=stdout,stderr=stderr)
 rec={'path':r['path'],'candidato':r['candidato'],'sha256_candidato':sha(raw),'request':{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())},'response':{'path':str(response.relative_to(ROOT)),'sha256':sha(response.read_bytes())},'returncode':run.returncode}
 if run.returncode:
  rec.update(aprovado=False,erro=err.read_text());results.append(rec);blocked=bool(re.search(r'\b(?:401|403|429)\b',rec['erro']));break
 render=response.read_text();source=r['fonte_html_decodificada'];assert sha(source.encode())==r['sha256_html'];norm=source;q=proof[r['path']]
 for c in sorted(q['administrativos_excluidos'],key=lambda c:c['inicio'],reverse=True):assert source[c['inicio']:c['fim']]==c['paragrafo_html'] and sha(c['paragrafo_html'].encode())==c['sha256_paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
 for code in q['codigos_contiguos_proprios_excluidos']:assert norm.count(code)==1;norm=norm.replace(code,'',1)
 a=v.texto_visivel_html(norm);b=v.texto_visivel_html(render);sl=Lists();sl.feed(norm);ml=Lists();ml.feed(render);st=Matrices();st.feed(norm);mt=Matrices();mt.feed(render);sm=st.result();mm=mt.result();sp=Visivel();sp.feed(norm);mp=Visivel();mp.feed(render);tests={'texto_pontuacao':a==b,'assinatura_numerica':v.assinatura_numerica(a)==v.assinatura_numerica(b),'contextos_numericos':contexto_numerico(a)==contexto_numerico(b),'listas_type_start_value':sl.events==ml.events,'matrizes_tabelas':sm==mm,'eventos_rowspan_colspan':sp.structure==mp.structure};rec.update(aprovado=all(tests.values()),checks=tests,sha256_html_fonte=r['sha256_html'],sha256_visivel_fonte=sha(a.encode()),sha256_visivel_github=sha(b.encode()),listas_fonte=sl.events,listas_github=ml.events,matrizes_fonte=sm,matrizes_github=mm,administrativos_excluidos=q['administrativos_excluidos'],codigos_contiguos_proprios_excluidos=q['codigos_contiguos_proprios_excluidos']);results.append(rec);print('GitHub',i,r['path'],tests,flush=True)
result={'escopo':'Onze POST restantes da autorização original de doze renders GitHub markdown; o primeiro payload acima de 400 KB foi recusado e não é retentado, somente render, sem publicação ou nova fonte governamental. Nenhum retry.','sha256_guard_vivo_ao_render':guardsha,'sha256_insumo_nativos12':sha(sourcepath.read_bytes()),'resumo':{'chamadas':len(results),'aprovados':sum(r['aprovado'] for r in results),'divergencias':sum(not r['aprovado'] for r in results),'bloqueio':blocked},'registros':results,'limites':'Preserva requests/responses integrais. Compara texto literal, sinais, números/contextos, ol/ul/li/type/start/value e matrizes de células com rowspan/colspan e grade expandida. CSS/classes podem ser sanitizados; não afirma identidade visual CSS nem revisão humana universal.'};(D/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert len(results)==11 and all(r['aprovado'] for r in results)
