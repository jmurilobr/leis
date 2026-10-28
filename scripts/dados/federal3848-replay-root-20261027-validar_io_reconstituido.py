from pathlib import Path
from html.parser import HTMLParser
import json,gzip,re,hashlib,sys,types,datetime
BASE=RUNTIME;ROOT=REPO_ROOT;sys.path.insert(0,str(ROOT/'scripts'))
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
from integridade_html_federal import Visivel
from preparar_lote_decretos_cache import fields
from identidade_decreto import extrair_epigrafe_decreto,numero_normalizado
import auditar
sha=lambda b:hashlib.sha256(b).hexdigest();mod=types.ModuleType('semantic');hf=ROOT/'federal/_provas_commonmark_cumulativo015018_20261021_001/commonmark-listas-helper.py.txt';exec(compile(hf.read_text(),str(hf),'exec'),mod.__dict__)
class Lists(HTMLParser):
 def __init__(self):super().__init__();self.events=[]
 def handle_starttag(self,t,a):
  if t in ['ol','ul','li']:self.events.append(('inicio',t,tuple(sorted(a))))
 def handle_endtag(self,t):
  if t in ['ol','ul','li']:self.events.append(('fim',t))
rows=json.loads((BASE/'preparo.json').read_text())['publicaveis'];renders={r['path']:r for r in json.loads((BASE/'render_output.json').read_text())['registros']};out=[];bad=[]
for r in rows:
 pr=r['proof'];src=ARCHIVE[r['path']]['html_original'];assert sha(src.encode())==r['sha256_fonte_html']==pr['sha256_fonte_html'];norm=src;ad=pr['marcador_administrativo_excluido'];cuts=ad['paragrafos'] if ad else []
 for c in sorted(cuts,key=lambda c:c['inicio'],reverse=True):assert src[c['inicio']:c['fim']]==c['paragrafo_html'] and sha(c['paragrafo_html'].encode())==c['sha256_paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
 codes=[]
 for m in reversed(list(re.finditer(r'###DEC-(\d+)-([A-Za-z0-9]+)-000-(\d\d)-(\d\d)-(\d{4})@@@',norm))):
  if m.start()<norm.lower().find('<body'):continue
  n,c,d,mo,y=m.groups();num=str(int(n))+('' if c=='0' else '-'+c)
  if numero_normalizado(num)==numero_normalizado(r['epigrafe']['numero']) and y+'-'+mo+'-'+d==r['epigrafe']['data']:codes.append(m.group());norm=norm[:m.start()]+norm[m.end():]
 a=v.texto_visivel_html(norm);q=renders[r['path']];sl=Lists();sl.feed(norm);ml=Lists();ml.feed(q['html']);lp=[]
 parser_error=None
 if r['HTML_original'] or sl.events:
  b=v.texto_visivel_html(q['html']);lok=sl.events==ml.events and not q['listas_ordenadas']
 else:
  try:
   parser=mod.Semantic(q['listas_ordenadas']);parser.feed(q['html']);assert parser.i==len(q['listas_ordenadas']);lp=parser.proof;lok=all(z['mesmo_numero'] for l in lp for z in l['itens']);b=v.texto_visivel_html(''.join(parser.parts))
  except (AssertionError,IndexError,KeyError,ValueError) as e:
   parser_error=type(e).__name__+': '+str(e);lok=False;b=v.texto_visivel_html(q['html'])
 for n in pr['normalizacoes_apresentacao']:b=b.replace(n['markdown'],n['fonte'],1)
 sp=Visivel();sp.feed(norm);mp=Visivel();mp.feed(q['html']);raw=ARCHIVE[r['path']]['md_final'].encode();assert sha(raw)==r['sha256'];meta,_,body=fields(raw.decode());ep=extrair_epigrafe_decreto('\n\n'.join(v.texto_visivel_html(p) for p in re.findall(r'<p\b[^>]*>[\s\S]*?</p>',body,re.I)[:8])) if r['HTML_original'] else extrair_epigrafe_decreto(body);assert ep and ep['data']==r['epigrafe']['data'] and ep['numero']==numero_normalizado(r['epigrafe']['numero']);errors,warnings=auditar.validar(raw.decode(),r['path'],datetime.date.today());ok=a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and lok and sp.structure==mp.structure and not sp.visual and not mp.visual and not errors and not warnings
 rec={'path':r['path'],'sha256_md_final':r['sha256'],'sha256_html':sha(src.encode()),'sha256_render':sha(q['html'].encode()),'sha256_visivel_fonte':sha(a.encode()),'sha256_visivel_render':sha(b.encode()),'aprovado':ok,'HTML_original':r['HTML_original'],'listas_contadores':lp,'listas_nativas':sl.events,'erro_parser_listas':parser_error,'administrativos_excluidos':cuts,'codigos_contiguos_proprios_excluidos':codes,'normalizacoes_apresentacao':pr['normalizacoes_apresentacao']};out.append(rec)
 if not ok:bad.append(dict(rec,visivel_fonte=a,visivel_render=b,erros_formato=errors,avisos_formato=warnings,listas_iguais=lok,tabelas_iguais=sp.structure==mp.structure))
res={'resumo':{'auditados':len(out),'aprovados':sum(r['aprovado'] for r in out),'divergencias':len(bad)},'registros':out,'divergencias':bad,'limites':'Replay independente marked 17.0.5, números/contextos e estrutura; não afirma identidade visual CSS ou revisão humana universal. Replay cumulativo privado de 022–024; alertas não são aprovados por este relatório.'};p=BASE/'resultado.json';assert not p.exists();p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['resumo'])
