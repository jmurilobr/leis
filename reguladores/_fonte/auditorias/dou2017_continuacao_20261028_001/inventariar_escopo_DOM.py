"""Inventário somente leitura de raízes e irmãos do campo normativo HTML5."""
from pathlib import Path
import sys,json,gzip,hashlib,re,collections
B=Path(__file__).resolve().parent;R=B.parents[3];D=B/'pacote3060_001';C=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo';sys.path[:0]=[str(C),str(R/'scripts/bin/qa-html5-20261027/python')];import html5lib
from comparadores_HTML5_snapshot import visible,matrices,lists
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'manifesto3060.json').read_bytes());rows=[];types=collections.Counter()
for part in m['primarias_partes']:
 for line in gzip.open(R/part['path'],'rt'):
  p=json.loads(line);src=p['HTML_utf8'];fragment=re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)',src,re.S)[0];full=html5lib.parse(src,treebuilder='etree',namespaceHTMLElements=False);frag=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);roots=[e for e in full.iter()if'texto-dou'in re.split(r'[\t\n\f\r ]+',e.attrib.get('class',''))];froots=[e for e in frag.iter()if'texto-dou'in re.split(r'[\t\n\f\r ]+',e.attrib.get('class',''))];r={'path':p['path'],'sha256_MD':p['sha256_md'],'sha256_HTML':p['sha256_fonte'],'raizes_full':len(roots),'raizes_fragmento':len(froots),'corpo_integral_igual':False,'irmaos':[]}
  if len(roots)==len(froots)==1:
   r['corpo_integral_igual']=visible(roots[0])==visible(froots[0])and matrices(roots[0])==matrices(froots[0])and lists(roots[0])==lists(froots[0]);parents={c:p for p in full.iter()for c in p};siblings=list(parents[roots[0]]);pos=siblings.index(roots[0]);body=frag.find('body');children=list(body);r['corpo_texto_solto']=bool((body.text or'').strip());r['raiz_e_primeiro_filho']=bool(children and children[0]is froots[0]);r['caudas_textuais']=any((e.tail or'').strip()for e in children)
   for j,e in enumerate(children[1:],1):
    original=siblings[pos+j]if pos+j<len(siblings)else None;key=str(e.tag)+' '+str(e.attrib);types[key]+=1;r['irmaos'].append({'tag':str(e.tag),'atributos':e.attrib,'texto_literal':visible(e),'mesmo_irmao_no_DOM_completo':original is not None and e.tag==original.tag and e.attrib==original.attrib and visible(e)==visible(original)and matrices(e)==matrices(original)and lists(e)==lists(original)})
  rows.append(r)
  if len(rows)%500==0:print(len(rows),flush=True)
result={'examinados':len(rows),'corpos_com_divergencia':sum(not r['corpo_integral_igual']for r in rows),'tipos_irmaos':dict(types),'registros':rows,'limites':'Não remove conteúdo, não relaxa comparadores, não aprova lacunas. Confronta raiz normativa inteira e irmãos exatos, por texto/sinais/listas/matrizes HTML5; sem equivalência visual CSS.'};(B/'inventario_escopo_DOM3060.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['examinados'],result['corpos_com_divergencia'],types,flush=True)
