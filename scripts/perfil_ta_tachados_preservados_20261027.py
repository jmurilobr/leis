"""Perfil privado sucessor: preserva tachados explícitos nos dispositivos ativos.

Não decide que o trecho tachado é histórico ou revogado. Desativação explícita
do dispositivo continua selecionada pela edição pública SAPL. CSS aplicado
complexo, ocultação ou fonte especial exigem revisão; CSS externo não é buscado.
"""
from pathlib import Path
from html.parser import HTMLParser
import collections,hashlib,json,re,sys
from lxml import html as lhtml
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts')]
from markdown_it import MarkdownIt
from html2md import convert
from converter_organica_fortaleza import Dispositivos
from auditar_commonmark_ta_v2 import AtivosIndependentes,Counters,headings_comprovados,assinatura_numerica,VOID
from diagnosticar_css_glifos_ta_20261027 import analisar as css_analisar
from conferir_tabelas_nativas_ta import conferir as conferir_tabelas

def sha(raw):return hashlib.sha256(raw).hexdigest()
def compact(s):return ''.join(s.split())

class FonteCompleta(AtivosIndependentes):
 def __init__(self):super().__init__();self.chars=[];self.visible=[];self.tabelas=0
 def handle_starttag(self,tag,attrs):
  super().handle_starttag(tag,attrs)
  if tag=='table' and self.stack and self.stack[-1]['active']:self.tabelas+=1
 def handle_data(self,text):
  if self.stack and self.stack[-1]['active']:
   self.visible.append(text)
   self.chars.extend((c,bool(self.stack[-1]['struck'])) for c in text if not c.isspace())

class RenderCompleto(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.chars=[]
 def handle_starttag(self,tag,attrs):
  struck=bool(self.stack and self.stack[-1][1]) or tag in {'s','del','strike'} or 'line-through' in dict(attrs).get('style','').lower()
  if tag not in VOID:self.stack.append((tag,struck))
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:del self.stack[i:];break
 def handle_data(self,text):self.chars.extend((c,bool(self.stack and self.stack[-1][1])) for c in text if not c.isspace())
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in VOID:self.handle_endtag(tag)

def runs(chars):
 out=[];start=None
 for i,(_,flag) in enumerate(chars+[(None,False)]):
  if flag and start is None:start=i
  elif not flag and start is not None:
   out.append(dict(inicio=start,fim=i,texto=''.join(c for c,_ in chars[start:i])));start=None
 return out

def inventario_markup(fragment,active_ids=None):
 doc=lhtml.fromstring(fragment);roots=[doc] if active_ids is None else [e for e in doc.iter() if e.get('id') in active_ids]
 out=[]
 for root in roots:
  for e in root.iter():
   if e.tag in {'s','del','strike'} or 'line-through' in e.get('style','').lower():out.append(dict(tag=e.tag,atributos=dict(e.attrib),texto=e.text_content()))
 return out

def comparar(source,body):
 p=FonteCompleta();p.feed(source);p.close()
 if not p.ativos or p.listas_nativas:raise ValueError('Área ativa ausente ou lista HTML nativa requer revisão própria')
 engine=MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough');tokens=engine.parse(body);rendered=engine.render(body)
 lists=[dict(start=t.attrGet('start') or 1,markup=t.markup,linhas=t.map) for t in tokens if t.type=='ordered_list_open'];counters=Counters(lists);counters.feed(rendered)
 q=RenderCompleto();q.feed(''.join(counters.out));q.close();source_chars=p.chars;render_chars=q.chars
 a=''.join(c for c,_ in source_chars);b=''.join(c for c,_ in render_chars)
 # Apenas os separadores de heading já comprovados literalmente pelo replay
 # anterior podem ser retirados. Nunca remove um sinal literal da fonte.
 from pe_fidelidade_visivel import texto_visivel_html
 normalized,changes=headings_comprovados(texto_visivel_html(''.join(counters.out)),body,' '.join(p.visible),engine)
 for change in changes:
  target=compact(change['markdown']);replacement=compact(change['fonte']);assert target.replace('—','',1)==replacement
  current=''.join(c for c,_ in render_chars);pos=current.find(target);assert pos>=0
  offset=pos+target.index('—');assert render_chars[offset]==('—',False)
  del render_chars[offset]
 b=''.join(c for c,_ in render_chars)
 assert b==compact(normalized)
 text_ok=a==b;mask_ok=source_chars==render_chars;number_ok=assinatura_numerica(a)==assinatura_numerica(b)
 source_markup=inventario_markup(source,set(p.ativos));render_markup=inventario_markup(rendered)
 def context(markup):
  result=[]
  for item in markup:
   attributes=tuple(sorted((k,v) for k,v in item['atributos'].items() if k in {'title','cite','datetime','aria-label'}))
   if attributes:result.append((item['tag'],compact(item['texto']),attributes))
  return collections.Counter(result)
 attributes_ok=context(source_markup)==context(render_markup)
 mismatch=next((i for i,(x,y) in enumerate(zip(source_chars,render_chars)) if x!=y),min(len(source_chars),len(render_chars)))
 tableproof=conferir_tabelas(source,body) if p.tabelas else None
 return dict(aprovado=text_ok and mask_ok and number_ok and attributes_ok,igualdade_caracteres_nao_brancos=text_ok,assinatura_numerica_confere=number_ok,marcacao_tachado_por_caractere_confere=mask_ok,atributos_contextuais_tachados_conferem=attributes_ok,tachados_fonte=runs(source_chars),tachados_renderizados=runs(render_chars),markup_tachado_fonte=source_markup,markup_tachado_renderizado=render_markup,ativos=p.ativos,historicos_excluidos=p.historicos,normalizacoes_heading=changes,listas=counters.proofs,prova_tabelas=tableproof,sha256_visivel_fonte=sha(a.encode()),sha256_visivel_renderizado=sha(b.encode()),sha256_html_renderizado=sha(rendered.encode()),contexto=None if mask_ok else dict(indice=mismatch,fonte=source_chars[max(0,mismatch-35):mismatch+75],renderizado=render_chars[max(0,mismatch-35):mismatch+75]))

def converter(source):
 parsed=Dispositivos();parsed.feed(source);parsed.close()
 if parsed.atual:raise ValueError('Dispositivo incompleto')
 body='\n\n'.join(part for block in parsed.ativos if (part:=convert(block['html'],exclude_struck=False)).strip())
 css=css_analisar(source,source.encode(),'perfil_privado','sem_MD','fonte_fornecida','perfil_privado')
 for event in css['eventos_texto_efetivo_DOM']:
  if event['escopo'] not in {'ativo','epigrafe'}:continue
  mso=event.get('mso_hide_nao_padronizado')
  if event['fonte_especial_aplicada_css'] or event['ocultacao_css'] or mso and mso['value'].lower()=='all':raise ValueError('Fonte especial/ocultação aplicada exige revisão própria')
 for rule in css['regras_CSS_examinadas']:
  if any(rule.get('matches_por_estado',{}).get(s,0) for s in ['ativo','epigrafe']) and any(d['name'] in {'text-decoration','text-decoration-line'} for d in rule['declarations']):raise ValueError('Tachado/override por regra CSS embutida exige revisão própria')
 pending_selectors={r['selector'] for r in css['regras_CSS_examinadas'] if any(r.get('matches_por_estado',{}).get(s,0) for s in ['ativo','epigrafe'])}
 pending=css['regras_condicionais_com_match']+css['pseudo_elementos_com_match']
 if css['seletores_nao_resolvidos'] or any(r['selector'] in pending_selectors for r in pending):raise ValueError('CSS condicional ou não resolvido exige revisão')
 proof=comparar(source,body)
 if not proof['atributos_contextuais_tachados_conferem']:raise ValueError('Atributos contextuais do tachado exigem preservação própria')
 if not proof['aprovado']:raise ValueError('Texto ou marcação de tachados diverge: '+json.dumps(proof['contexto'],ensure_ascii=False))
 parsed.prova_tachados_preservados=proof
 return body,parsed
