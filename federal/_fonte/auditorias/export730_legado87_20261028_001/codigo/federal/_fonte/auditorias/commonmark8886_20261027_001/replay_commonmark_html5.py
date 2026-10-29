"""Replay local integral de 8.886/1942: CommonMark independente + árvore HTML5.

Sem rede; não altera pacote, canônico, guard ou pendência. Reutiliza somente as
remoções administrativas e normalizações já comprovadas no pacote congelado.
"""
from pathlib import Path
import sys,json,gzip,hashlib,re,datetime,importlib.metadata
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
for p in ['scripts/bin/qa-20261027/python','scripts/bin/qa-html5-20261027/python','scripts']:sys.path.insert(0,str(ROOT/p))
from markdown_it import MarkdownIt
import markdown_it,html5lib
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
sha=lambda b:hashlib.sha256(b).hexdigest();B=ROOT/'federal/_fonte/auditorias/retomada_federal_20261027_004/cumulativo022024_v2';path='federal/decretos/1942/dec-8886-1942-03-02.md';idx=json.loads((B/'entrega3848-artefatos-hashes.json').read_text())['arquivos'];expected={r['path']:r['sha256'] for r in idx}
for name in ['nativos12_revisao_ROOT.json','resultado.json']:
 p=B/name;assert sha(p.read_bytes())==expected[str(p.relative_to(ROOT))]
r=next(x for x in json.loads((B/'nativos12_revisao_ROOT.json').read_text())['registros'] if x['path']==path);proof=next(x for x in json.loads((B/'resultado.json').read_text())['registros'] if x['path']==path);raw=r['md_candidato_utf8'].encode();source=r['fonte_html_decodificada'];assert sha(raw)==r['sha256_candidato']==proof['sha256_md_final'] and sha(source.encode())==r['sha256_html']==proof['sha256_html'];cab,body=raw.decode()[4:].split('\n---\n',1);title,sep,payload=body.lstrip().partition('\n');assert sep and title.startswith('# Decreto nº 8.886 ');norm=source
for c in sorted(proof['administrativos_excluidos'],key=lambda c:c['inicio'],reverse=True):
 assert source[c['inicio']:c['fim']]==c['paragrafo_html'] and sha(c['paragrafo_html'].encode())==c['sha256_paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
for code in proof['codigos_contiguos_proprios_excluidos']:assert norm.count(code)==1;norm=norm.replace(code,'',1)
engine=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False});render=engine.render(payload);a=v.texto_visivel_html(norm);b=v.texto_visivel_html(render);normalizations=[]
for n in proof['normalizacoes_apresentacao']:
 before=b;b=b.replace(n['markdown'],n['fonte'],1);normalizations.append(dict(n,aplicada_neste_render=before!=b))
assert sha(a.encode())==proof['sha256_visivel_fonte']
BLOCK={'address','article','aside','blockquote','br','caption','dd','div','dl','dt','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hr','li','main','nav','ol','p','pre','section','table','tbody','td','tfoot','th','thead','tr','ul'};SKIP={'head','script','style','title'}
def tag(el):return el.tag.rsplit('}',1)[-1].lower() if isinstance(el.tag,str) else ''
def visible(el):
 parts=[]
 def walk(n):
  t=tag(n)
  if not t or t in SKIP:return
  if t in BLOCK:parts.append(' ')
  if n.text:parts.append(n.text)
  for child in n:
   walk(child)
   if child.tail:parts.append(child.tail)
  if t in BLOCK:parts.append(' ')
 walk(el);return ' '.join(''.join(parts).replace('\ufeff','').split())
def ancestor(n,parents,wanted):
 n=parents.get(n)
 while n is not None:
  if tag(n) in wanted:return n
  n=parents.get(n)
 return None
def matrices(tree):
 parents={child:parent for parent in tree.iter() for child in parent};out=[]
 for ti,table in enumerate(tree.iter('table')):
  rows=[n for n in table.iter('tr') if ancestor(n,parents,{'table'}) is table];grid={};records=[]
  for y,row in enumerate(rows):
   x=0;cells=[]
   for ci,cell in enumerate([n for n in row if tag(n) in {'td','th'}]):
    while (y,x) in grid:x+=1
    rs_raw=cell.attrib.get('rowspan');cs_raw=cell.attrib.get('colspan');rs=int(rs_raw or '1');cs=int(cs_raw or '1');assert rs>0 and cs>0
    rec={'tag':tag(cell),'rowspan_literal':rs_raw,'colspan_literal':cs_raw,'rowspan':rs,'colspan':cs,'texto':visible(cell),'linha':y,'coluna':x};cells.append(rec)
    for yy in range(y,y+rs):
     for xx in range(x,x+cs):assert (yy,xx) not in grid;grid[(yy,xx)]={'origem':[y,x],'texto':rec['texto'],'tag':rec['tag']}
    x+=cs
   records.append({'grupo_HTML5':tag(parents[row]),'celulas':cells})
  h=max((y for y,x in grid),default=-1)+1;w=max((x for y,x in grid),default=-1)+1;out.append({'tabela':ti,'linhas':records,'ocupacao_por_spans':[[grid.get((y,x)) for x in range(w)] for y in range(h)]})
 return out

def alpha(n):
 out=''
 while n>0:n,j=divmod(n-1,26);out=chr(65+j)+out
 return out

def roman(n):
 out=''
 for value,s in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
  q,n=divmod(n,value);out+=s*q
 return out

def lists(tree):
 parents={child:parent for parent in tree.iter() for child in parent};tables=list(tree.iter('table'));out=[]
 for node in tree.iter():
  if tag(node) not in {'ol','ul'}:continue
  kind=tag(node);typ=node.attrib.get('type');start=node.attrib.get('start');count=int(start or '1') if kind=='ol' else None;items=[]
  for li in [n for n in node if tag(n)=='li']:
   value=li.attrib.get('value');num=int(value) if value is not None else count;marker=None
   if kind=='ol':
    marker=alpha(num) if typ in ['A','a'] and num>0 else roman(num) if typ in ['I','i'] and 0<num<4000 else str(num)
    if typ in ['a','i']:marker=marker.lower()
    count=num+1
   items.append({'value_literal':value,'contador_HTML':num,'marcador_intrinseco_sem_CSS':marker,'texto':visible(li)})
  cell=ancestor(node,parents,{'td','th'});table=ancestor(node,parents,{'table'});out.append({'tag':kind,'type_literal':typ,'start_literal':start,'tabela_ancestral':tables.index(table) if table is not None else None,'celula_ancestral_texto':visible(cell) if cell is not None else None,'itens':items})
 return out
st=html5lib.parse(norm,treebuilder='etree',namespaceHTMLElements=False);rt=html5lib.parse(render,treebuilder='etree',namespaceHTMLElements=False);a5=visible(st.find('body'));b5=visible(rt.find('body'))
for n in proof['normalizacoes_apresentacao']:b5=b5.replace(n['markdown'],n['fonte'],1)
sm,rm=matrices(st),matrices(rt);sl,rl=lists(st),lists(rt)
checks={'texto_pontuacao_mesmo_comparador_anterior':a==b,'assinatura_numerica_anterior':v.assinatura_numerica(a)==v.assinatura_numerica(b),'contextos_numericos_anteriores':contexto_numerico(a)==contexto_numerico(b),'texto_pontuacao_HTML5':a5==b5,'assinatura_numerica_HTML5':v.assinatura_numerica(a5)==v.assinatura_numerica(b5),'contextos_numericos_HTML5':contexto_numerico(a5)==contexto_numerico(b5),'listas_HTML5_type_start_value_contadores':sl==rl,'matrizes_HTML5_linha_celula_spans':sm==rm}
assert len(sm)==20
for name,data in [('fonte_original.html.gz',gzip.compress(source.encode(),mtime=0)),('md_final.md.gz',gzip.compress(raw,mtime=0)),('fonte_normalizada.html.gz',gzip.compress(norm.encode(),mtime=0)),('render_commonmark.html',render.encode())]:
 p=D/name;assert not p.exists();p.write_bytes(data)
(D/'proof8886_congelada.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');(D/'matrizes_HTML5.json').write_text(json.dumps({'fonte':sm,'render_commonmark':rm},ensure_ascii=False,indent=2)+'\n');(D/'listas_HTML5.json').write_text(json.dumps({'fonte':sl,'render_commonmark':rl},ensure_ascii=False,indent=2)+'\n')
result={'escopo':'Complemento local independente para o corpo oficial completo de 8.886/1942, não subdividido. Exclui somente frontmatter/título editorial e usa as remoções/normalizações já comprovadas no pacote fechado. Nenhuma rede, instalação ou alteração de canônico/guard/máscara.','path':path,'sha256_md_final':sha(raw),'sha256_html_original':sha(source.encode()),'bytes_corpo_oficial_UTF8':len(payload.encode()),'sha256_payload':sha(payload.encode()),'sha256_render_commonmark':sha(render.encode()),'motores':{'markdown_it_py':importlib.metadata.version('markdown-it-py'),'preset':'commonmark','html':True,'linkify':False,'typographer':False,'html5lib':html5lib.__version__,'python':sys.version},'checks':checks,'aprovado':all(checks.values()),'resumo':{'corpos_completos':1,'tabelas_HTML5':len(sm),'linhas_HTML5':sum(len(t['linhas']) for t in sm),'celulas_HTML5':sum(len(row['celulas']) for t in sm for row in t['linhas']),'listas_HTML5':len(sl),'divergencias':sum(not x for x in checks.values())},'normalizacoes_apresentacao':normalizations,'sha256_visivel_anterior_fonte':sha(a.encode()),'sha256_visivel_anterior_commonmark':sha(b.encode()),'sha256_visivel_HTML5_fonte':sha(a5.encode()),'sha256_visivel_HTML5_commonmark':sha(b5.encode()),'fontes_de_insumo':[{'path':str((B/name).relative_to(ROOT)),'sha256':sha((B/name).read_bytes())} for name in ['nativos12_revisao_ROOT.json','resultado.json']],'sha256_guard_vivo_registrado':sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes()),'codigos_comparadores':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in [ROOT/'scripts/estados/pe_fidelidade_visivel.py',ROOT/'scripts/auditar_pontuacao_federal.py']],'limites':'O limite GitHub de 400 KB permanece: isto não é validação GitHub integral. Compara texto/sinais/números/contextos, listas intrínsecas e matrizes do DOM HTML5; não executa JavaScript, CSS ou layout visual. Cada célula mantém texto, posição e spans literais, além de ocupação derivada dos spans.'};(D/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['resumo']);print(checks);assert all(checks.values())
