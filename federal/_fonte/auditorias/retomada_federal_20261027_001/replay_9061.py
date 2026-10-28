import json,gzip,hashlib,sys,types,re
from pathlib import Path
from html.parser import HTMLParser
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from preparar_lote_decretos_cache import fields
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
from integridade_html_federal import Visivel
from identidade_decreto import numero_normalizado
sha=lambda b:hashlib.sha256(b).hexdigest();verified=json.loads((BASE/'verificacao_9061.json').read_text());rs=verified['registros'];assert len(rs)==9061
if sys.argv[1]=='preparar':
 inp=[]
 for r in rs:
  raw=(ROOT/r['arquivo_final']).read_bytes();assert sha(raw)==r['sha256_md_final'];body=fields(raw.decode())[2].lstrip().partition('\n')[2];inp.append({'path':r['path'],'markdown':body})
 p=BASE/'render_9061_input.json';assert not p.exists();p.write_text(json.dumps(inp));print('preparados',len(inp));raise SystemExit
assert sys.argv[1]=='validar'
helper=ROOT/'federal/_provas_commonmark_cumulativo015018_20261021_001/commonmark-listas-helper.py.txt';mod=types.ModuleType('semantic_archived');exec(compile(helper.read_text(),str(helper),'exec'),mod.__dict__)
class Lists(HTMLParser):
 def __init__(self):super().__init__();self.events=[]
 def handle_starttag(self,t,a):
  if t in ['ol','ul','li']:self.events.append(('inicio',t,tuple(sorted(a))))
 def handle_endtag(self,t):
  if t in ['ol','ul','li']:self.events.append(('fim',t))
proofs={}
for f in ['federal/_auditoria_commonmark_cumulativo015018_20261021_001.json.gz','federal/_auditoria_commonmark_cumulativo019_20261021_001.json.gz']:
 for r in json.loads(gzip.decompress((ROOT/f).read_bytes()))['registros']:proofs[r['path']]=r
render=json.loads((BASE/'render_9061_output.json').read_text());assert render['versao']=='17.0.5';qmap={r['path']:r for r in render['registros']};assert len(qmap)==9061
out=[];errors=[]
for i,r in enumerate(rs,1):
 pr=proofs[r['path']];assert pr['sha256_md']==r['sha256_md_final'];src=gzip.decompress((ROOT/r['fonte_html_cache']).read_bytes()).decode();assert sha(src.encode())==r['sha256_html']==pr['sha256_fonte_html'];norm=src
 for c in sorted(pr['administrativos_excluidos'],key=lambda c:c['inicio'],reverse=True):
  assert src[c['inicio']:c['fim']]==c['paragrafo_html'] and sha(c['paragrafo_html'].encode())==c['sha256_paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
 codes=[]
 for m in reversed(list(re.finditer(r'###DEC-(\d+)-([A-Za-z0-9]+)-000-(\d\d)-(\d\d)-(\d{4})@@@',norm))):
  if m.start()<norm.lower().find('<body'):continue
  n,c,d,mo,y=m.groups();num=str(int(n))+('' if c=='0' else '-'+c)
  if numero_normalizado(num)==r['numero'] and y+'-'+mo+'-'+d==r['data']:codes.append(m.group());norm=norm[:m.start()]+norm[m.end():]
 assert codes==pr['codigos_contiguos_proprios_excluidos'];q=qmap[r['path']];a=v.texto_visivel_html(norm);sl=Lists();sl.feed(norm);ml=Lists();ml.feed(q['html']);listok=False
 if pr['HTML_original']:b=v.texto_visivel_html(q['html']);listok=sl.events==ml.events
 else:
  parser=mod.Semantic(q['listas_ordenadas']);parser.feed(q['html']);assert parser.i==len(q['listas_ordenadas']);listok=not sl.events and all(z['mesmo_numero'] for l in parser.proof for z in l['itens']);b=v.texto_visivel_html(''.join(parser.parts))
 for n in pr['normalizacoes_apresentacao']:b=b.replace(n['markdown'],n['fonte'],1)
 sp=Visivel();sp.feed(norm);mp=Visivel();mp.feed(q['html']);h=sha(q['html'].encode());ok=a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and listok and sp.structure==mp.structure and not sp.visual and not mp.visual and h==pr['sha256_render_html'] and sha(a.encode())==pr['sha256_visivel_fonte'];out.append({'path':r['path'],'sha256_md_final':r['sha256_md_final'],'sha256_html_fonte':r['sha256_html'],'sha256_render':h,'sha256_visivel_fonte':sha(a.encode()),'sha256_visivel_render':sha(b.encode()),'aprovado':ok,'HTML_original':pr['HTML_original']})
 if not ok:errors.append(r['path'])
 if i%1000==0:print('replay',i,'/',len(rs),'divergências',len(errors),flush=True)
res={'escopo':'Replay integral novo dos 9.061 candidatos congelados; não modifica canônicos, snapshots, planos ou registro. HTML renderizado novamente por marked 17.0.5 e comparado com fonte e provas históricas.','limite':'Contadores reais das listas e delimitadores literais do código confrontados; não afirma identidade visual CSS. Verificação automática integral, com revisões contextuais históricas separadas, sem alegação de leitura humana universal.','resumo':{'auditados':len(out),'aprovados':sum(r['aprovado'] for r in out),'divergencias':len(errors)},'registros':out,'divergencias':errors};p=BASE/'replay_9061_resultado.json';assert not p.exists();p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['resumo']);assert not errors
