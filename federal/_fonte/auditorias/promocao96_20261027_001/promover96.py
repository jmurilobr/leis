"""ROOT: valida 41 + 16 + 39 novos decretos; somente --apply publica arquivos locais.

Dry-run padrão, sem escrita. Nenhuma operação Git de escrita, rede ou registro.
"""
import sys
sys.dont_write_bytecode=True
import argparse,base64,datetime,gzip,hashlib,html,json,os,re,subprocess
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[3].resolve();sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-20261027/python'))
from baixar_camara import corpo_norma
from comum import decodificar
from html2md import convert
from preparar_lote_decretos_cache import fields
from identidade_decreto import extrair_epigrafe_decreto,numero_normalizado
from identidade_decreto_revisao import normal,FECHO,MESES
from integridade_html_federal import Visivel
from integridade_anexos_decreto import anexo_proprio_ausente
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
from markdown_it import MarkdownIt
import baixar_federal as f,auditar
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def safe(p):
 p=Path(p);assert not p.is_absolute() and '..' not in p.parts;joined=ROOT/p;resolved=joined.resolve();assert resolved.is_relative_to(ROOT) and resolved==joined;return resolved
def read(p):return json.loads(p.read_bytes())
def key(n):return re.sub(r'[.\s]','',str(n)).upper().lstrip('0') or '0'
def syncdir(p):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def durable(p,raw):
 with p.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
a=argparse.ArgumentParser(description=__doc__);a.add_argument('--apply',action='store_true');args=a.parse_args();receipt=read(B/'recibo96.json');assert sha(Path(__file__).read_bytes())==receipt['sha256_runner']
for r in receipt['insumos']:assert sha(safe(r['path']).read_bytes())==r['sha256'],r['path']
for pair in receipt['listas']:
 lp=safe(pair['paths']);hs=read(safe(pair['hashes']));assert sha(lp.read_bytes())==hs['sha256_lista'];assert lp.read_text().splitlines()==[r['path'] for r in hs['arquivos']]
 for r in hs['arquivos']:assert sha(safe(r['path']).read_bytes())==r['sha256'],r['path']
assert sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes())==receipt['sha256_guard74']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();allrows=[];provenance=[]
for package in receipt['pacotes']:
 manifest=read(safe(package['manifesto']));rows=manifest['publicaveis_privados'];assert len(rows)==package['aprovados'];ref=manifest[package['campo_fontes']];archive=safe(ref['path']);raw=archive.read_bytes();assert sha(raw)==ref['sha256'] and len(raw)<95*1024**2;proofs=[json.loads(x) for x in gzip.decompress(raw).splitlines()];assert len(proofs)==package['fontes'];records={}
 for proof in proofs:
  source=proof['fontes_completas_anteriores'] if package['revisao_individual'] else proof
  path=source['fila']['path'];assert path not in records;records[path]=(proof,source)
  assert sha(source['metadados_raw'].encode())==source['fila']['sha256_metadados_raw']
  for sourcefile in source['fontes_completas']:assert sha(base64.b64decode(sourcefile['bytes_originais_base64'],validate=True))==sourcefile['recibo']['sha256_raw']
 for r in rows:
  proof,source=records[r['path']];assert proof['candidato_aprovado']==r;assert proof['replay']['aprovado'] is True
  final=proof['md_final_utf8'].encode();assert sha(final)==r['sha256_candidato'] and safe(r['candidato']).read_bytes()==final
  allrows.append((r,source,proof,final,package['revisao_individual']))
 provenance.extend([safe(package['manifesto']),archive])
assert len(allrows)==96;paths=set();urns=set();identities=set();prepared=[];renders=[]
for r,source,proof,raw,individual in allrows:
 path=r['path'];assert not safe(path).exists(),('Destino já existe no disco',path)
 match=re.fullmatch(r'federal/decretos/(\d{4})/dec-(\d+)-(\d{4}-\d\d-\d\d)\.md',path);assert match
 d=r['indice_senado'];front,_,body=fields(raw.decode());identity=(key(front['numero']),front['data'][:4]);assert identity==(key(match[2]),match[1]);assert front['data']==match[3];assert path not in paths and front['urn'] not in urns and identity not in identities;paths.add(path);urns.add(front['urn']);identities.add(identity)
 api=json.loads(source['metadados_raw']);assert api['legislationIdentifier']==front['urn']==r['urn'];assert api['legislationDate']==front['data'];assert api['legislationType'] in {'Decreto','Decreto Numerado'} and not api.get('encoding');assert sha(source['metadados_raw'].encode())==front['sha256_metadados_fonte']==r['sha256_metadados'];assert front['tipo']=='Decreto';assert front['urn']=='urn:lex:br:federal:decreto:'+front['data']+';'+str(front['numero']);assert key(d['numero'])==identity[0] and d['dataassinatura']==datetime.date.fromisoformat(front['data']).strftime('%d/%m/%Y')
 pr=source['coleta'];original=next(x for x in source['fontes_completas'] if x['papel']=='texto_original');page=decodificar(base64.b64decode(original['bytes_originais_base64']),'text/html');assert sha(page.encode())==r['sha256_fonte_html_decodificada'];assert original['recibo']==pr['texto_original'];assert front['fonte']==original['recibo']['url'];catalog=next(x for x in source['fontes_completas'] if x['papel']=='pagina_norma');catalog_html=decodificar(base64.b64decode(catalog['bytes_originais_base64']),'text/html');links=[html.unescape(x) for x in re.findall(r'href=["\']([^"\']+)["\']',catalog_html)];from urllib.parse import urljoin,urlparse
 assert front['fonte'] in {urljoin(catalog['recibo']['url'],x) for x in links};assert urlparse(front['fonte']).hostname in {'www.camara.leg.br','www2.camara.leg.br'} and '-publicacaooriginal-' in front['fonte'] or urlparse(front['fonte']).hostname in {'www.camara.leg.br','www2.camara.leg.br'} and '-textopublicacaooriginal-' in front['fonte']
 headers=[]
 for m in re.finditer(r'<h1\b[^>]*>(.*?)</h1>',page,re.I|re.S):
  text=v.texto_visivel_html(m[1]);ep=extrair_epigrafe_decreto(text)
  if ep and ep['numero']==identity[0] and ep['data']==front['data']:headers.append(text)
 assert len(headers)==1;body_html=corpo_norma(page);area='<h1>'+html.escape(headers[0])+'</h1>\n'+body_html;assert area==r['area_normativa_html'],'Extração normativa diverge'
 title,sep,payload=body.lstrip().partition('\n');assert sep and title.startswith('# Decreto ');expected=headers[0]+'\n\n'+convert(body_html);assert payload.strip()==expected.strip(),'Corpo candidato diverge da conversão integral congelada'
 sp=Visivel();sp.feed(area);assert not sp.visual and not re.search(r'<(?:ol|ul|li)\b',area,re.I);assert not anexo_proprio_ausente(expected,sp);partial=f.motivo_texto_parcial_decreto('DEC-n',expected)
 if individual:
  review=proof['parecer'];assert review['path']==path and review['parecer']=='comando_decisorio_proprio_integral_para_replay';assert review['sha256_html_raw']==original['recibo']['sha256_raw'];assert sha(convert(body_html).encode())==review['sha256_corpo_convertido'];assert partial=='Sem artigo normativo próprio; íntegra/comando decisório exige revisão específica';assert 'RESOLVE' in normal(v.texto_visivel_html(body_html)) and 'GETULIO VARGAS' in normal(v.texto_visivel_html(body_html))
 else:assert not partial,(path,partial)
 text=v.texto_visivel_html(body_html);last=max([x.start() for x in re.finditer(r'\b(?:Art\.?\s*\d+|Artigo\s+[úu]nico)',text,re.I)] or ([0] if individual else [-1]));assert last>=0;tail=normal(text[last:]);closing=[]
 for m in re.finditer(r'(?:RIO DE JANEIRO|BRASILIA)[,.;\s]+(?:EM\s*)?(?:DE\s*)?\d{1,2}[º°]?\s*(?:DE\s*)?[A-Z]+\s*[,;]?\s*(?:DE\s*)?[12]\.?\d{3}',tail):
  fm=FECHO.match(m[0]);assert fm;closing.append({'literal_normalizado':m[0],'data':datetime.date(int(fm['ano'].replace('.','')),MESES[fm['mes']],int(fm['dia'])).isoformat()})
 assert len(closing)==1 and closing[0]==r['fecho_proprio'] and closing[0]['data']==front['data'];assert not re.search(r'\b(?:ANEXO|REGULAMENTO|CONVENCAO)\b',tail[:tail.find(closing[0]['literal_normalizado'])]);errors,warnings=auditar.validar(raw.decode(),path,datetime.date.today());assert not errors and not warnings,(errors,warnings);renders.append({'path':path,'markdown':payload,'area':area});prepared.append({'path':path,'raw':raw,'sha256':sha(raw),'candidato':r['candidato']})
# Replay independente do corpo inteiro em dois motores, sem arquivos temporários.
code="import {marked} from '/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));";marked={r['path']:r['html'] for r in json.loads(subprocess.check_output(['node','--input-type=module','-e',code],input=json.dumps(renders).encode()))};cm=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False})
for r in renders:
 a=v.texto_visivel_html(r['area']);sp=Visivel();sp.feed(r['area'])
 for rendered in [marked[r['path']],cm.render(r['markdown'])]:
  b=v.texto_visivel_html(rendered);mp=Visivel();mp.feed(rendered);assert a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and sp.structure==mp.structure and not mp.visual and not re.search(r'<(?:ol|ul|li)\b',rendered,re.I),r['path']
query=subprocess.run(['git','cat-file','--batch-check'],cwd=ROOT,input=''.join(head+':'+p+'\n' for p in sorted(paths)),text=True,capture_output=True,check=True);assert len(query.stdout.splitlines())==96 and all(x.endswith(' missing') for x in query.stdout.splitlines())
years=sorted({y for n,y in identities});tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--']+['federal/decretos/'+y for y in years],cwd=ROOT)
for path in tree.decode().split('\0'):
 m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d\.md',path)
 if m:assert (key(m[2]),m[1]) not in identities,('Colisão número/ano em HEAD',path)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head
print('Validados 96 novos destinos: 41 + 16 + 39; fontes/CRC/extração/identidade/fechos/guard/replay duplo e ausência no HEAD '+head+'. Nenhuma escrita.',flush=True)
if not args.apply:raise SystemExit(0)
D=B/('aplicacao_ROOT_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));D.mkdir(exist_ok=False);backups=[]
for i,r in enumerate(prepared,1):
 p=D/(f'{i:03}_'+Path(r['path']).name+'.candidato');durable(p,r['raw']);assert sha(p.read_bytes())==r['sha256'];backups.append({'path':r['path'],'candidato':r['candidato'],'backup_candidato':str(p.relative_to(ROOT)),'sha256_final':r['sha256'],'preimagem':'ausente'})
for i,p in enumerate(provenance,1):durable(D/(f'fonte_{i:02}_'+p.name),p.read_bytes())
durable(D/'intencao.json',(json.dumps({'HEAD':head,'novas_inclusoes':backups,'recibo_validado':receipt},ensure_ascii=False,indent=2)+'\n').encode());syncdir(D)
for r in prepared:
 target=safe(r['path']);assert not target.exists(),r['path'];target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name('.'+target.name+f'.promocao96.{os.getpid()}.tmp');durable(temp,r['raw']);assert sha(temp.read_bytes())==r['sha256'];os.link(temp,target);temp.unlink();syncdir(target.parent);assert sha(target.read_bytes())==r['sha256']
 with (D/'aplicacao.jsonl').open('a') as log:log.write(json.dumps({'path':r['path'],'sha256_final':r['sha256'],'estado':'criado atomicamente sem sobrescrever destino'},ensure_ascii=False)+'\n');log.flush();os.fsync(log.fileno())
assert all(sha(safe(r['path']).read_bytes())==r['sha256'] for r in prepared);syncdir(D);print('ROOT: 96 arquivos criados e conferidos; backups, fontes e recibos em',D,flush=True)
