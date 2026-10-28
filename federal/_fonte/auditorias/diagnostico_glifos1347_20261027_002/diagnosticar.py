"""CSS/glifos: inspeção estática contextual, nenhuma máscara ou edição normativa."""
from pathlib import Path
import sys,json,gzip,hashlib,base64,re,subprocess,collections
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;ROOT=B.parents[3]
for p in ['scripts','scripts/bin/qa-20261027/python','scripts/bin/qa-html5-20261027/python']:sys.path.insert(0,str(ROOT/p))
import tinycss2,cssselect2,html5lib
from comum import decodificar
from identidade_decreto import extrair_epigrafe_decreto
sha=lambda b:hashlib.sha256(b).hexdigest();docs=[];inputs=[]
def read(p):
 raw=p.read_bytes();inputs.append({'path':str(p.relative_to(ROOT)),'sha256':sha(raw)});return json.loads(raw)
# Read only frozen primary archives, never capture caches.
receipt=read(B.parent/'promocao145_20261027_001/recibo145.json')
for pack in receipt['pacotes']:
 manifest=read(ROOT/pack['manifesto'])
 if pack.get('reparo_6223'):
  raw=gzip.decompress((ROOT/manifest['fonte_prova']['path']).read_bytes());source=json.loads(raw)['fonte_original_completa'];r={**manifest,'sha256_candidato':manifest['sha256_final']};pairs=[(r,source)]
 else:
  archive=manifest[pack['campo_fontes']];data=(ROOT/archive['path']).read_bytes();assert sha(data)==archive['sha256'];proofs=[json.loads(x) for x in gzip.decompress(data).splitlines()];by={}
  for proof in proofs:
   src=proof['fontes_completas_anteriores'] if pack['revisao_individual'] else proof;by[src['fila']['path']]=src
  pairs=[(r,by[r['path']]) for r in manifest['publicaveis_privados']]
 for r,src in pairs:
  file=next(x for x in src['fontes_completas'] if x['papel']=='texto_original');raw=base64.b64decode(file['bytes_originais_base64']);assert sha(raw)==file['recibo']['sha256_raw'];docs.append({'path':r['path'],'lote':'145','sha256_candidato':r['sha256_candidato'],'candidato':r['candidato'],'source_raw':raw,'source':decodificar(raw,'text/html'),'source_url':file['recibo']['url'],'api_raw':src['metadados_raw'],'normalizacao':None})
for dirname,packet,label in [('alimentacao_normas_20261027_008','pacote_final003','454'),('alimentacao_normas_20261027_009','pacote_final001','748')]:
 D=B.parent/dirname/packet;m=read(D/'lote_final.json');mapping=read(ROOT/m['fontes_publicas_integrais']['mapa']);by={r['path']:r for r in m['publicaveis_privados']}
 for part in mapping['partes']:
  data=(ROOT/part['path']).read_bytes();assert sha(data)==part['sha256_gzip']
  for line in gzip.decompress(data).splitlines():
   p=json.loads(line);r=p['registro'];assert r==by[r['path']];raw=base64.b64decode(p['html_original_base64']);assert sha(raw)==r['sha256_html'];docs.append({'path':r['path'],'lote':label,'sha256_candidato':r['sha256_candidato'],'candidato':r['candidato'],'source_raw':raw,'source':raw.decode(),'source_url':r['fontes']['texto']['url'],'api_raw':p['metadados_raw'],'normalizacao':p['normalizacao_administrativa']})
assert len(docs)==1347 and len({r['path'] for r in docs})==1347
special=re.compile(r'symbol|wingdings?|webdings?|dingbats?',re.I)
props={'font-family','font','display','visibility','opacity','color','font-size','text-decoration','text-decoration-line','mso-hide'}
def declarations(content):
 out=[]
 for d in tinycss2.parse_declaration_list(content,skip_comments=True,skip_whitespace=True):
  if d.type=='declaration' and d.lower_name in props:out.append({'name':d.lower_name,'value':tinycss2.serialize(d.value).strip(),'important':bool(d.important)})
 return out
def danger(d):
 name=d['name'];v=d['value'].lower();return bool(name in {'font','font-family'} and special.search(v) or name in {'text-decoration','text-decoration-line'} and 'line-through' in v or name=='display' and v=='none' or name=='visibility' and v in {'hidden','collapse'} or name=='opacity' and re.fullmatch(r'0+(?:\.0+)?',v) or name=='color' and ('transparent' in v or re.search(r'rgba\([^)]*,\s*0(?:\.0*)?\s*\)',v)) or name=='font-size' and re.fullmatch(r'0+(?:\.0+)?(?:px|pt|em|rem|%)?',v) or name=='mso-hide' and v=='all')
def text_of(el):return ''.join(el.itertext()).strip()
def node_signature(el):return {'tag':el.tag,'id':el.get('id'),'class':el.get('class'),'style':el.get('style'),'face':el.get('face')}
def analyze(doc):
 tree=html5lib.parse(doc['source'],treebuilder='etree',namespaceHTMLElements=False);wrapper=cssselect2.ElementWrapper.from_html_root(tree);elements=list(wrapper.iter_subtree());body=next(e for e in elements if e.etree_element.tag=='body');parents={e.etree_element:e.parent.etree_element if e.parent else None for e in elements};normroots=[e.etree_element for e in elements if 'textoNorma' in e.classes] if doc['lote']=='145' else [body.etree_element]
 if not normroots:normroots=[body.etree_element]
 normset=set()
 for root in normroots:normset.update(root.iter())
 for e in elements:
  if e.etree_element.tag=='h1' and extrair_epigrafe_decreto(text_of(e.etree_element)):normset.update(e.etree_element.iter())
 admin_labels=[x['marcador'] for x in (doc['normalizacao'] or {}).get('paragrafos',[])]
 def scope(el,text):
  if any(text.strip()==s for s in admin_labels):return 'administrativo_comprovado'
  return 'normativo' if el in normset else 'fora_da_area_normativa'
 matcher=cssselect2.Matcher();rules=[];unsupported=[];fontfaces=[];order=0
 def parse_rules(nodes,conditional=None):
  nonlocal order
  for rule in nodes:
   if rule.type=='qualified-rule':
    decl=declarations(rule.content)
    if not decl:continue
    selector=tinycss2.serialize(rule.prelude).strip();item={'selector':selector,'declarations':decl,'conditional':conditional,'matches_normative':0,'matches_other':0,'dangerous':any(danger(d) for d in decl)};rules.append(item);order+=1;item['order']=order
    try:
     for compiled in cssselect2.compile_selector_list(selector):matcher.add_selector(compiled,item)
    except Exception as exc:
     if item['dangerous']:unsupported.append({'selector':selector,'declarations':decl,'conditional':conditional,'erro':str(exc)})
   elif rule.type=='at-rule':
    name=rule.lower_at_keyword
    if name=='font-face':
     decl=declarations(rule.content or []);fontfaces.extend(d for d in decl if d['name']=='font-family' and special.search(d['value']))
    elif rule.content is not None and name in {'media','supports','layer','document'}:
     parse_rules(tinycss2.parse_rule_list(rule.content,skip_comments=True,skip_whitespace=True),(conditional+' / ' if conditional else '')+'@'+name+' '+tinycss2.serialize(rule.prelude))
 for e in elements:
  if e.etree_element.tag=='style':parse_rules(tinycss2.parse_stylesheet(e.etree_element.text or '',skip_comments=True,skip_whitespace=True))
 styles={};events=[];conditional_matches=[];inline_interesting=[];pseudo=[]
 for e in elements:
  el=e.etree_element;parent=e.parent.etree_element if e.parent else None;inherit=styles.get(parent,{});applied={}
  def put(d,rank,origin):
   name=d['name'];name='font-family' if name=='font' else name
   if name not in applied or rank>=applied[name]['rank']:applied[name]={'value':d['value'],'rank':rank,'origin':origin,'property_original':d['name']}
  if el.get('face'):put({'name':'font-family','value':el.get('face')},(False,0,0,0,0,-1),{'presentational_face':el.get('face')})
  for specificity,matchorder,pseudoname,item in matcher.match(e):
   item['matches_normative' if el in normset else 'matches_other']+=1
   if item['conditional'] or pseudoname:
    if item['dangerous'] and el in normset:
     (pseudo if pseudoname else conditional_matches).append({'selector':item['selector'],'pseudo':pseudoname,'conditional':item['conditional'],'declarations':item['declarations'],'node':node_signature(el),'texto_contextual':text_of(el)[:250]})
    continue
   for d in item['declarations']:put(d,(d['important'],0,*specificity,item['order']),{'selector':item['selector'],'declaration':d})
  for d in declarations(el.get('style','')):
   put(d,(d['important'],1,0,0,0,0),{'inline_style':el.get('style'),'declaration':d})
   if danger(d):inline_interesting.append({'node':node_signature(el),'declaration':d,'escopo':scope(el,text_of(el)),'texto_contextual':text_of(el)[:300]})
  computed={}
  for name in ['font-family','font-size','color','visibility']:
   if name in applied:
    x=applied[name];computed[name]=inherit.get(name) if x['value'].lower() in {'inherit','unset'} else x
   else:computed[name]=inherit.get(name)
  for name in ['display','opacity','text-decoration','text-decoration-line','mso-hide']:computed[name]=applied.get(name)
  computed['ancestor_hidden']=list(inherit.get('ancestor_hidden',[]));computed['ancestor_strike']=list(inherit.get('ancestor_strike',[]));computed['s_del_ancestors']=list(inherit.get('s_del_ancestors',[]))
  if el.tag in {'s','del','strike'}:computed['s_del_ancestors'].append(node_signature(el))
  for name in ['display','opacity']:
   x=computed.get(name)
   if x and danger({'name':name,'value':x['value']}):computed['ancestor_hidden'].append({'property':name,**x})
  if 'hidden' in el.attrib:computed['ancestor_hidden'].append({'property':'hidden','value':el.get('hidden'),'origin':node_signature(el)})
  for name in ['text-decoration','text-decoration-line']:
   x=computed.get(name)
   if x and 'line-through' in x['value'].lower():computed['ancestor_strike'].append({'property':name,**x})
  styles[el]=computed
  # Own text and child tails use this element's cascade; descendant overrides
  # must not cause the parent's subtree to be reported with the wrong font.
  segments=[el.text or '']+[child.tail or '' for child in el]
  if el.tag in {'script','style','head','title'}:continue
  for text in segments:
   if not text.strip():continue
   font=computed.get('font-family');hidden=list(computed['ancestor_hidden']);strike=list(computed['ancestor_strike']);tags=computed['s_del_ancestors']
   for name in ['visibility','color','font-size']:
    x=computed.get(name)
    if x and danger({'name':name,'value':x['value']}):hidden.append({'property':name,**x})
   fs=bool(font and special.search(font['value']));mso=computed.get('mso-hide')
   if not(fs or hidden or strike or tags or mso and danger({'name':'mso-hide','value':mso['value']})):continue
   events.append({'escopo':scope(el,text),'texto_literal':text,'codepoints':['U+%04X'%ord(c) for c in text.strip()[:24]],'fonte_especial_aplicada_css':font if fs else None,'ocultacao_css':hidden,'tachado_css':strike,'tags_s_del_strike':tags,'mso_hide_nao_padronizado':mso,'node':node_signature(el)})
 unused=[{'selector':r['selector'],'declarations':r['declarations'],'conditional':r['conditional'],'matches_normative':r['matches_normative'],'matches_other':r['matches_other']} for r in rules if r['dangerous'] and not r['matches_normative']]
 external=[el.etree_element.get('href') for el in elements if el.etree_element.tag=='link' and 'stylesheet' in (el.etree_element.get('rel') or '').lower()]
 return {'path':doc['path'],'lote':doc['lote'],'sha256_candidato':doc['sha256_candidato'],'sha256_HTML_primario':sha(doc['source_raw']),'sha256_API':sha(doc['api_raw'].encode()),'fonte_HTML':doc['source_url'],'font_face_declarados_sem_provar_uso':fontfaces,'regras_perigosas_sem_match_normativo':unused,'seletores_nao_resolvidos':unsupported,'regras_condicionais_com_match':conditional_matches,'pseudo_elementos_com_match':pseudo,'inline_interessantes':inline_interesting,'eventos_texto_efetivo_DOM':events,'stylesheets_externas_nao_consultadas':external}
lexical=[]
for doc in docs:
 if special.search(doc['source']):lexical.append({'path':doc['path'],'trechos':[doc['source'][max(0,m.start()-120):m.end()+120] for m in special.finditer(doc['source'])]})
(B/'triagem_lexical_independente.json').write_text(json.dumps(lexical,ensure_ascii=False,indent=2)+'\n')
results=[];evidence=[]
for i,doc in enumerate(docs,1):
 assert sha((ROOT/doc['candidato']).read_bytes())==doc['sha256_candidato'];row=analyze(doc);results.append(row)
 if any(e['escopo']=='normativo' for e in row['eventos_texto_efetivo_DOM']) or row['seletores_nao_resolvidos'] or row['regras_condicionais_com_match'] or row['pseudo_elementos_com_match']:evidence.append({'diagnostico':row,'HTML_primario_base64':base64.b64encode(doc['source_raw']).decode(),'metadados_raw':doc['api_raw']})
 if i%100==0:print('Analisados',i,flush=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();data=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=''.join(head+':'+r['path']+'\n' for r in results).encode());pos=0
for r in results:
 end=data.index(b'\n',pos);h=data[pos:end].split();pos=end+1
 if h[-1]==b'missing':r['HEAD_atual']='ausente';continue
 assert h[1]==b'blob';size=int(h[2]);blob=data[pos:pos+size];pos+=size+1;r['HEAD_atual']={'HEAD':head,'OID':h[0].decode(),'sha256_MD':sha(blob),'igual_candidato':sha(blob)==r['sha256_candidato']}
assert pos==len(data);summary={'atos':len(results),'por_lote':dict(collections.Counter(r['lote'] for r in results)),'com_fontes_especiais_em_texto_normativo':sum(any(e['escopo']=='normativo' and e['fonte_especial_aplicada_css'] for e in r['eventos_texto_efetivo_DOM']) for r in results),'com_ocultacao_css_em_texto_normativo':sum(any(e['escopo']=='normativo' and e['ocultacao_css'] for e in r['eventos_texto_efetivo_DOM']) for r in results),'com_tachado_css_ou_tags_em_texto_normativo':sum(any(e['escopo']=='normativo' and (e['tachado_css'] or e['tags_s_del_strike']) for e in r['eventos_texto_efetivo_DOM']) for r in results),'atos_com_fontface_especial_declarado':sum(bool(r['font_face_declarados_sem_provar_uso']) for r in results),'atos_com_condicionais_ou_seletores_pendentes':sum(bool(r['seletores_nao_resolvidos'] or r['regras_condicionais_com_match'] or r['pseudo_elementos_com_match']) for r in results),'fontes_com_prova_integral_adicional':len(evidence),'mascaras_aplicadas':0,'canônicos_alterados':0}
(B/'fontes_provas_contextos.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in evidence)+'\n').encode(),mtime=0));result={'resumo':summary,'HEAD_observado':head,'insumos':inputs,'motores':{'tinycss2':tinycss2.__version__,'cssselect2':cssselect2.__version__,'html5lib':html5lib.__version__},'registros':results,'limites':'Inspeção estática do DOM HTML5 e regras CSS internas, com cascata/importância/especificidade/herança para as propriedades examinadas. Segmentos próprios e tails evitam atribuir fonte ancestral ao filho que a sobrescreve. Não executa JavaScript, consulta fontes de caracteres ou CSS externas, nem resolve @media/@supports; tais regras ficam separadas como condicionais. Fontes especiais em texto não comprovam equivalência dos glifos pelo Unicode. @font-face e estilos sem match não provam uso. Propriedades mso não são tratadas como CSS padrão. Sem alteração de fontes/candidatos/guard ou máscaras.'};(B/'diagnostico1347.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(summary,flush=True)
