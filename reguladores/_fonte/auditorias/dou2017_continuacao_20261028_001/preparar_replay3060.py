from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;R=B.parents[3];D=B/'pacote3060_001';A=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002';sha=lambda b:hashlib.sha256(b).hexdigest();s=(A/'replay5769_portavel.py').read_text();s=s.replace("C=D/'codigo'","C=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo'").replace('manifesto5769.json','manifesto3060.json').replace("(D/name).read_bytes()","(R/name).read_bytes()").replace("receipt=D/'entrega-hashes.json'","receipt=D/'recibo_replay.json'")
s=s.replace("(D/'baseline_publico_atual.json.gz')","(R/m['baseline_reguladores']['path'])").replace("(D/'indice_transversal_v2.json.gz')","(R/m['baseline_federal']['path'])").replace('len(expected)==5769','len(expected)==3060')
a=s.index("classification={");z=s.index('rows=source_rows()',a)
s=s[:a]+'''def source_rows():
 for part in m['primarias_partes']:
  path=R/part['path'];assert sha(path.read_bytes())==part['sha256_gzip'];count=0
  with gzip.open(path,'rt')as f:
   for line in f:
    p=json.loads(line);count+=1;assert p['path']in expected;yield p
  assert count==part['registros']
'''+s[z:]
s=s.replace("assert classification[path]['status']!='reserva_tipo_numero_serie_inconclusivos',path","assert not typ or num,path;assert typ or not re.search(r'congresso nacional|senado federal|camara dos deputados',n(org)),path")
point=" st=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);paras="
extra=""" full_dom=html5lib.parse(p['HTML_utf8'],treebuilder='etree',namespaceHTMLElements=False);roots=[e for e in full_dom.iter()if 'texto-dou'in re.split(r'[\\t\\n\\f\\r ]+',e.attrib.get('class',''))];assert len(roots)==1
 fragment_dom=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False)
 assert visible(roots[0])==visible(fragment_dom.find('body')) and matrices(roots[0])==matrices(fragment_dom) and lists(roots[0])==lists(fragment_dom),(path,'Extração integral do HTML normativo diverge do DOM completo')
"""
assert point in s;s=s.replace(point,extra+point);a=s.index('assert len(done)==5769');s=s[:a]+'''assert len(done)==3060 and set(done)==set(expected)
held=[json.loads(l)for l in gzip.decompress((D/'provas_retencoes3.jsonl.gz').read_bytes()).splitlines()];assert len(held)==3 and not(set(done)&{r['registro']['path']for r in held})
for item in held:
 p=item['prova_integral'];r=item['registro'];assert sha(p['MD_utf8'].encode())==r['sha256_md']and sha(p['HTML_utf8'].encode())==r['sha256_html']
assert len(m['retidos_qualificacao'])+len(held)==940
print(json.dumps({'selecionados_reproduzidos':len(done),'retidos_totais':940,'retidos_contexto_orgao_novos':3,'entrada':4000,'canônicos_ou_reservados_no_indice':index['MD_canonicos_ou_reservados'],'reservas_sem_chave_preservadas':len(index['reservas']),'HTTP':0,'escritas_canonicas':0,'limites':'Não é dedup universal; chaves explícitas, reservas e jurisdições preservadas. Replays pontuação/HTML5/listas/tabelas/DOM normativo completo. Sem vigência, CSS visual, ano completo ou revisão humana universal.'},ensure_ascii=False),flush=True)
'''
(D/'replay3060.py').write_text(s);compile(s,str(D/'replay3060.py'),'exec');m=json.loads((D/'manifesto3060.json').read_bytes());m['codigo']={str(p.relative_to(R)):sha(p.read_bytes())for p in(A/'codigo').iterdir()if p.is_file()};(D/'manifesto3060.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');(D/'recibo_replay.json').write_text(json.dumps({'arquivos_proprios':[{'path':str((D/f).relative_to(R)),'sha256':sha((D/f).read_bytes())}for f in ['manifesto3060.json','replay3060.py','provas_retencoes3.jsonl.gz','inventario_cadeias3063.json','mapa_fontes.json']]+[{'path':x['path'],'sha256':x['sha256']}for x in [m['baseline_reguladores'],m['baseline_federal']]]},indent=2)+'\n')
