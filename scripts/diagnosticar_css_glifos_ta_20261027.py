"""Suplemento municipal privado de CSS/glifos; predicado federal congelado.

Não consulta CSS/fontes externas, altera textos ou conclui vigência. A adaptação
se limita ao escopo de dispositivos SAPL, estados e inventário de fontes CSS.
"""
from pathlib import Path
import argparse,ast,collections,hashlib,json,re,sys
R=Path(__file__).resolve().parent.parent
for p in ['scripts','scripts/bin/qa-20261027/python','scripts/bin/qa-html5-20261027/python','scripts/bin/qa-confaz-20261027/python']:sys.path.insert(0,str(R/p))
import tinycss2,cssselect2,html5lib
from auditar_commonmark_ta_v2 import AtivosIndependentes
from comum import decodificar
FED=R/'federal/_fonte/auditorias/diagnostico_glifos1347_20261027_002/diagnosticar.py'
FED_SHA='beadf267d897ef287c7525935f833c73d8b7337a58db27b6fc43a0f5cc62a4e2'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def carregar():
 source=FED.read_text();assert sha(source.encode())==FED_SHA
 tree=ast.parse(source);names={'declarations','danger','text_of','node_signature'}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'special','props'} for t in n.targets)]
 assert len(nodes)==6
 env=dict(re=re,tinycss2=tinycss2,cssselect2=cssselect2,html5lib=html5lib,sha=sha,collections=collections)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'predicado_federal_congelado','exec'),env)
 original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='analyze');body=ast.get_source_segment(source,original)
 patches=[]
 def change(old,new):
  nonlocal body
  assert body.count(old)==1,old
  body=body.replace(old,new);patches.append(dict(antes=old,depois=new))
 change("normroots=[e.etree_element for e in elements if 'textoNorma' in e.classes] if doc['lote']=='145' else [body.etree_element]", "normroots=[e.etree_element for e in elements if 'dptt' in e.classes or e.etree_element.tag=='h1' and 'page-header' in e.classes]")
 change(" if not normroots:normroots=[body.etree_element]", " if not normroots:raise ValueError('Área dispositiva municipal ausente')")
 change("  if e.etree_element.tag=='h1' and extrair_epigrafe_decreto(text_of(e.etree_element)):normset.update(e.etree_element.iter())", "  if e.etree_element.tag=='h1' and 'page-header' in e.classes:normset.update(e.etree_element.iter())")
 change("  return 'normativo' if el in normset else 'fora_da_area_normativa'", "  cursor=el\n  while cursor is not None:\n   ident=cursor.get('id')\n   if ident in doc['ativos']:return 'ativo'\n   if ident in doc['historicos']:return 'historico_desativado'\n   if cursor.tag=='h1' and 'page-header' in (cursor.get('class') or '').split():return 'epigrafe'\n   cursor=parents.get(cursor)\n  return 'fora_da_area_normativa'")
 change("   item['matches_normative' if el in normset else 'matches_other']+=1", "   item['matches_normative' if el in normset else 'matches_other']+=1\n   state=scope(el,text_of(el));item.setdefault('matches_por_estado',{});item['matches_por_estado'][state]=item['matches_por_estado'].get(state,0)+1")
 change("styles={};events=[];conditional_matches=[];inline_interesting=[];pseudo=[]", "styles={};events=[];conditional_matches=[];inline_interesting=[];pseudo=[];font_uses=collections.Counter();font_examples={}")
 change("   fs=bool(font and special.search(font['value']));mso=computed.get('mso-hide')", "   fs=bool(font and special.search(font['value']));mso=computed.get('mso-hide')\n   if font and el in normset:\n    key=(scope(el,text),font['value']);font_uses[key]+=1\n    if len(font_examples.setdefault(key,[]))<3:font_examples[key].append(dict(texto=text,origem=font['origin'],node=node_signature(el)))")
 change("'stylesheets_externas_nao_consultadas':external}", "'stylesheets_externas_nao_consultadas':external,'regras_CSS_examinadas':rules,'fontes_CSS_efetivas':[dict(escopo=k[0],familia=k[1],segmentos=v,exemplos=font_examples[k]) for k,v in font_uses.items()]}")
 exec(compile(body,'analisador_federal_adaptado_ao_escopo_TA','exec'),env)
 return env['analyze'],patches

ANALYZE,PATCHES=carregar()

def analisar(source,raw,path,mdsha,url,label):
 p=AtivosIndependentes();p.feed(source);p.close()
 assert p.ativos
 result=ANALYZE(dict(source=source,source_raw=raw,path=path,lote=label,sha256_candidato=mdsha,source_url=url,api_raw='{}',normalizacao=None,ativos=set(p.ativos),historicos=set(p.historicos)))
 result.pop('sha256_API');result['ativos']=p.ativos;result['historicos_desativados']=p.historicos;result['tachados_explicitos_selecionador_independente']=p.tachados
 tree=html5lib.parse(source,treebuilder='etree',namespaceHTMLElements=False)
 labels=[]
 for el in tree.iter():
  if el.get('id') in p.ativos and 'revogado' in (el.get('class') or '').split():
   text=' '.join(el.itertext());labels.append(dict(id=el.get('id'),texto=text,rotulo_literal_revogado=bool(re.search(r'\brevogad[oa]\b',text,re.I))))
 result['dispositivos_ativos_classe_revogado']=labels
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifesto',type=Path,action='append',required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();a.saida.mkdir(exist_ok=False,parents=True)
 reports=[];seen=set();inputs=[]
 for manifest in a.manifesto:
  m=json.loads(manifest.read_text());mapping=Path(m['mapeamento_fontes']);rows=json.loads(mapping.read_text());names=set(Path(m['lista_normas']).read_text().splitlines());assert names=={r['path'] for r in rows};inputs.append(dict(manifesto=str(manifest),sha256=sha(manifest.read_bytes()),mapa=str(mapping),sha256_mapa=sha(mapping.read_bytes()),normas=m['normas']))
  for r in rows:
   assert r['path'] not in seen;seen.add(r['path']);proof=r.get('prova_frontend') or r['fonte'];raw=Path(proof['arquivo']).read_bytes();assert sha(raw)==proof['sha256'];assert sha(Path(r['path']).read_bytes())==r['sha256']
   report=analisar(decodificar(raw,proof['content_type']),raw,r['path'],r['sha256'],proof['url_final'],str(m['normas']));report['fonte_arquivo']=proof['arquivo'];reports.append(report)
   if len(reports)%100==0:print('Analisados',len(reports),flush=True)
 def count(test):return sum(any(test(e) for e in row['eventos_texto_efetivo_DOM']) for row in reports)
 active=lambda e:e['escopo'] in {'ativo','epigrafe'}
 summary=dict(normas=len(reports),fontes_especiais_ativas=count(lambda e:active(e) and e['fonte_especial_aplicada_css']),ocultacao_ativa=count(lambda e:active(e) and e['ocultacao_css']),tachado_ativo=count(lambda e:active(e) and (e['tachado_css'] or e['tags_s_del_strike'])),mso_hide_ativo=count(lambda e:active(e) and e['mso_hide_nao_padronizado']),condicionais_ou_seletores_pendentes=sum(bool(r['seletores_nao_resolvidos'] or r['regras_condicionais_com_match'] or r['pseudo_elementos_com_match']) for r in reports),mascaras=0,canonicos_alterados=0)
 result=dict(resumo=summary,entradas=inputs,predicado_federal=dict(path=str(FED.relative_to(R)),sha256=FED_SHA),adaptacoes_escopo=PATCHES,motores=dict(tinycss2=tinycss2.__version__,cssselect2=cssselect2.__version__,html5lib=html5lib.__version__),codigo_sha256=sha(Path(__file__).read_bytes()),registros=reports,limites='Cascata estática CSS embutido/inline com importância/especificidade/herança do predicado federal congelado; segmentos próprios/tails respeitam overrides. Ativo, histórico desativado, epígrafe e fora da área são separados. Não busca CSS ou fontes externas nem executa JavaScript. Família CSS especial configurada não prova equivalência do glifo pelo Unicode. @media/@supports/pseudo e seletores não resolvidos ficam separados. Predicado examina somente suas propriedades enumeradas, sem certificar todo efeito visual possível. Rótulo revogado não autoriza inferir revogação do ato inteiro.')
 (a.saida/'diagnostico.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
