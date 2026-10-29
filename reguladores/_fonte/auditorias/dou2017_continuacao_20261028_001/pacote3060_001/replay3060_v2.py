"""Replay somente leitura: usa arquivos do pacote, sem caches normativos ou /tmp."""
from pathlib import Path
import sys,json,gzip,hashlib,datetime,re,collections,subprocess,urllib.request
D=Path(__file__).resolve().parent;R=next(p for p in D.parents if (p/'scripts').is_dir() and (p/'reguladores').is_dir());C=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo';sys.path[:0]=[str(C),str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts/bin/qa-html5-20261027/python')]
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'manifesto3060.json').read_bytes())
for name,digest in m['codigo'].items():assert sha((R/name).read_bytes())==digest,name
receipt=D/'recibo_replay_v2.json'
if receipt.exists():
 for x in json.loads(receipt.read_bytes())['arquivos_proprios']:assert sha((R/x['path']).read_bytes())==x['sha256'],x['path']
def sem_HTTP(*a,**k):raise AssertionError('HTTP proibido neste replay')
urllib.request.urlopen=sem_HTTP
import auditar_cache_dou as audit
from epigrafe_tokens_html_privado import epigrafe_tokens
import gates_snapshot as gates
from comum import normalizar_chave
import pe_fidelidade_visivel as v
from integridade_html_federal import Visivel
from integridade_anexos_decreto import anexo_proprio_ausente
from markdown_it import MarkdownIt
from comparadores_HTML5_snapshot import visible,matrices,lists
from css_glifos_DOU_snapshot import analyze
import html5lib
audit.RAIZ=R;orig=audit.epigrafe_do_ato;audit.epigrafe_do_ato=lambda s,f,i:epigrafe_tokens(s,f,i,orig)
base=json.loads(gzip.decompress((R/m['baseline_reguladores']['path']).read_bytes()));known=set();urls=set();keys=collections.defaultdict(list);tracked=set()
for x in base['documentos']:
 known.add(audit.identidade(x['meta']));urls.add(x['meta'].get('fonte'));keys[gates.chave(x['meta'],x['path'])].append(x['path']);tracked.add(x['path'])
expected={x['path']:x for x in m['documentos']};assert len(expected)==3060
index=json.loads(gzip.decompress((R/m['baseline_federal']['path']).read_bytes()));federal_keys={(x['tipo'],x['numero'],x['data'])for x in index['registros']};federal_urns={x.get('URN_literal')for x in index['registros']+index['reservas']if x.get('URN_literal')};federal_urls={x.get('fonte_literal')for x in index['registros']+index['reservas']if x.get('fonte_literal')}
from gate_orgao import motivos as motivos_orgao,n
from identidade_cross_snapshot import number,ambiguous
def source_rows():
 for part in m['primarias_partes']:
  path=R/part['path'];assert sha(path.read_bytes())==part['sha256_gzip'];count=0
  with gzip.open(path,'rt')as f:
   for line in f:
    p=json.loads(line);count+=1;assert p['path']in expected;yield p
  assert count==part['registros']
rows=source_rows()
mdengine=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False}).enable('table').enable('strikethrough');intermediate=[];done=[]
for i,p in enumerate(rows,1):
 path=p['path'];raw=p['MD_utf8'].encode();src=p['HTML_utf8'].encode();r=expected[path];assert sha(raw)==p['sha256_md']==r['sha256_md'] and sha(src)==p['sha256_fonte']==r['sha256_html'];checked,meta=audit.conferir(R/path,known,urls,datetime.date(2026,10,28),bruto_md=raw,fonte_bytes=src);body=audit.meta_corpo(raw.decode())[1];assert not gates.motivos_identidade(meta,path,keys,urls,tracked) and not gates.motivos_conteudo(body);fragment=re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)',p['HTML_utf8'],re.S)[0];parsed=Visivel();parsed.feed(fragment);parsed.close();assert not parsed.visual and not anexo_proprio_ausente(body,parsed)
 org=meta.get('orgao');org_html=audit.campo_html(p['HTML_utf8'],'orgao-dou-data');plain=re.sub(r'<[^>]+>',' ',fragment);assert not motivos_orgao(org,org_html,plain),path;levels=[n(x)for x in org.split('/')];assert not any(len(levels)>1 and levels[0]==root and levels[1]==unit for root,unit in ambiguous),path
 typ=index['tipos_explicitamente_comparaveis'].get(n(meta['tipo']));num=number(meta['numero']);key=(typ,num,meta['data'])if typ and num else None;assert not key or key not in federal_keys,path;assert not meta.get('urn')or meta['urn']not in federal_urns;assert meta['fonte']not in federal_urls;assert not typ or num,path;assert typ or not re.search(r'congresso nacional|senado federal|camara dos deputados',n(org)),path
 css=analyze({'path':path,'lote':'DOU','sha256_candidato':sha(raw),'source_raw':src,'source':p['HTML_utf8'],'source_url':r['fonte'],'normalizacao':None});assert not any(e['escopo']=='normativo'for e in css['eventos_texto_efetivo_DOM']);assert not (css['seletores_nao_resolvidos']or css['regras_condicionais_com_match']or css['pseudo_elementos_com_match'])
 full_dom=html5lib.parse(p['HTML_utf8'],treebuilder='etree',namespaceHTMLElements=False);roots=[e for e in full_dom.iter()if 'texto-dou'in re.split(r'[\t\n\f\r ]+',e.attrib.get('class',''))];assert len(roots)==1
 fragment_dom=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False)
 fragment_body=fragment_dom.find('body');fragment_roots=[e for e in fragment_body.iter()if 'texto-dou'in re.split(r'[\t\n\f\r ]+',e.attrib.get('class',''))];assert len(fragment_roots)==1
 assert visible(roots[0])==visible(fragment_roots[0]) and matrices(roots[0])==matrices(fragment_roots[0]) and lists(roots[0])==lists(fragment_roots[0]),(path,'Corpo normativo integral diverge do DOM completo')
 parents={child:parent for parent in full_dom.iter()for child in parent};siblings=list(parents[roots[0]]);position=siblings.index(roots[0]);fragment_children=list(fragment_body);assert fragment_children and fragment_children[0]is fragment_roots[0] and not (fragment_body.text or '').strip()
 assert not any((e.tail or '').strip()for e in fragment_children)
 for j,extra in enumerate(fragment_children[1:],1):
  assert position+j<len(siblings);original=siblings[position+j];cls=set(re.split(r'[\t\n\f\r ]+',original.attrib.get('class','')))
  assert original.tag=='p' and 'assina'in cls or original.tag=='div' and 'informacao-conteudo-dou'in cls,(path,'Irmão externo não administrativo')
  assert original.tag==extra.tag and set(re.split(r'[\t\n\f\r ]+',extra.attrib.get('class','')))==cls and visible(original)==visible(extra) and matrices(original)==matrices(extra) and lists(original)==lists(extra),(path,'Conteúdo administrativo externo divergente')

 st=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);paras=[''.join(e.itertext()).strip()for e in st.iter()if e.tag in {'p','h1','h2','h3','h4','h5','h6'}];arts=[(j,t)for j,t in enumerate(paras)if re.match(r'^Art(?:igo)?\.?\s*(?:1(?:[ºo°.]|\b)|[úu]nico)\b',t,re.I)];assert arts;prefix=normalizar_chave('\n'.join(paras[:arts[0][0]]));assert not re.search(r'onde se le|leia[ -]se|retificac|retificar|retifica o|retifica a',prefix)
 rendered=mdengine.render(body);h1=re.search(r'<h1\b[^>]*>.*?</h1>',rendered,re.S);assert h1 and v.texto_visivel_html(h1[0])==' '.join(meta['titulo'].split());rendered=rendered[:h1.start()]+rendered[h1.end():];a=v.texto_visivel_html(fragment);b=v.texto_visivel_html(rendered);b,changes=v._heading_comprovado(b,body,a);assert a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b);rt=html5lib.parse(rendered,treebuilder='etree',namespaceHTMLElements=False);a5=visible(st.find('body'));b5=visible(rt.find('body'))
 for c in changes:b5=b5.replace(c['markdown'],c['fonte'],1)
 assert a5==b5 and matrices(st)==matrices(rt)and lists(st)==lists(rt)
 known.add(audit.identidade(meta));urls.add(meta['fonte']);keys[gates.chave(meta,path)].append(path);tracked.add(path);intermediate.append({'path':path,'markdown':body,'fragmento':fragment,'normalizacoes':changes});done.append(path)
 if i%250==0:print('CommonMark/CSS/identidade',i,flush=True)
# Módulo GFM exato está incluído no próprio pacote.
js="const {marked}=await import(process.argv[1]);let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));"
gfm={x['path']:x['html']for x in json.loads(subprocess.check_output(['node','--input-type=module','-e',js,(C/'marked.esm.mjs').as_uri()],input=json.dumps(intermediate).encode()))}
for z in intermediate:
 h=gfm[z['path']];h1=re.search(r'<h1\b[^>]*>.*?</h1>',h,re.S);assert h1;h=h[:h1.start()]+h[h1.end():];st=html5lib.parse(z['fragmento'],treebuilder='etree',namespaceHTMLElements=False);rt=html5lib.parse(h,treebuilder='etree',namespaceHTMLElements=False);a=visible(st.find('body'));b=visible(rt.find('body'))
 for c in z['normalizacoes']:b=b.replace(c['markdown'],c['fonte'],1)
 assert a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b)and matrices(st)==matrices(rt)and lists(st)==lists(rt)
assert len(done)==3060 and set(done)==set(expected)
held=[json.loads(l)for l in gzip.decompress((D/'provas_retencoes3.jsonl.gz').read_bytes()).splitlines()];assert len(held)==3 and not(set(done)&{r['registro']['path']for r in held})
for item in held:
 p=item['prova_integral'];r=item['registro'];assert sha(p['MD_utf8'].encode())==r['sha256_md']and sha(p['HTML_utf8'].encode())==r['sha256_html']
assert len(m['retidos_qualificacao'])+len(held)==940
print(json.dumps({'selecionados_reproduzidos':len(done),'retidos_totais':940,'retidos_contexto_orgao_novos':3,'entrada':4000,'canônicos_ou_reservados_no_indice':index['MD_canonicos_ou_reservados'],'reservas_sem_chave_preservadas':len(index['reservas']),'HTTP':0,'escritas_canonicas':0,'limites':'Não é dedup universal; chaves explícitas, reservas e jurisdições preservadas. Replays pontuação/HTML5/listas/tabelas/DOM normativo completo. Sem vigência, CSS visual, ano completo ou revisão humana universal.'},ensure_ascii=False),flush=True)
