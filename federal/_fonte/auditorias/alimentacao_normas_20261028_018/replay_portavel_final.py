"""Replay portátil dos aprovados: sem rede, /tmp, caches de captura ou escrita."""
from pathlib import Path
import sys,json,gzip,hashlib,base64,re,datetime,ast,subprocess
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-20261027/python'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-html5-20261027/python'))
sha=lambda b:hashlib.sha256(b).hexdigest();receipt=json.loads((B/'recibo_replay_portavel_final.json').read_bytes())
for r in receipt['codigos']:assert sha((ROOT/r['path']).read_bytes())==r['sha256'],r['path']
assert sha(Path(__file__).read_bytes())==receipt['sha256_runner']
import html5lib
from markdown_it import MarkdownIt
from preparar_lote_decretos_cache import fields
from identidade_decreto import extrair_epigrafe_decreto,numero_normalizado
from identidade_decreto_revisao import normal,FECHO,MESES
from integridade_html_federal import Visivel
from integridade_anexos_decreto import anexo_proprio_ausente
from auditar_pontuacao_federal import normalizar_marcador_administrativo,contexto_numerico
from estados import pe_fidelidade_visivel as v
import baixar_federal as f
D=B/'pacote_final001';manifest=json.loads((D/'lote_final.json').read_bytes());assert sha((D/'lote_final.json').read_bytes())==receipt['sha256_manifesto'];mapping=json.loads((ROOT/manifest['fontes_publicas_integrais']['mapa']).read_bytes());assert sha((ROOT/manifest['fontes_publicas_integrais']['mapa']).read_bytes())==manifest['fontes_publicas_integrais']['sha256_mapa'];baseline=(ROOT/manifest['baseline_anos']['path']).read_bytes();assert sha(baseline)==manifest['baseline_anos']['sha256'];known={}
for entry in gzip.decompress(baseline).split(b'\0'):
 if not entry:continue
 p=entry.split(b'\t',1)[1].decode();m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md',p)
 if m:known[(m[2].lstrip('0'),m[1])]=p
sourcecode=ROOT/'federal/_fonte/auditorias/commonmark8886_20261027_001/replay_commonmark_html5.py';tree=ast.parse(sourcecode.read_text());names={'tag','visible','ancestor','matrices','alpha','roman','lists'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'BLOCK','SKIP'} for t in n.targets)];assert len(nodes)==9;env={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sourcecode),'exec'),env);tree=ast.parse((B/'qualificar_snapshot_v4.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='principal_fechos');closing_env={'normal':normal,'FECHO':FECHO,'MESES':MESES,'v':v,'re':re,'datetime':datetime};exec(compile(ast.Module(body=[node],type_ignores=[]),'principal_fechos_congelado','exec'),closing_env);public={r['path']:r for r in manifest['publicaveis_privados']};assert len(public)==572;held={r['path'] for r in manifest['retencoes_contextuais']['registros']};assert len(held)==18 and not set(public)&held;assert len(public)==manifest['resumo']['publicaveis_privados'];positions={p['path']:0 for p in mapping['partes']};counts={p['path']:0 for p in mapping['partes']}
for part in mapping['partes']:
 data=(ROOT/part['path']).read_bytes();assert sha(data)==part['sha256_gzip'] and len(data)==part['bytes_gzip']<95*1024**2
rows=[];paths=set();urns=set();identities=set()
for rec in mapping['registros']:
 assert rec['offset_gzip']==positions[rec['arquivo']];positions[rec['arquivo']]+=rec['bytes_member_gzip'];counts[rec['arquivo']]+=1
 with (ROOT/rec['arquivo']).open('rb') as stream:stream.seek(rec['offset_gzip']);member=stream.read(rec['bytes_member_gzip'])
 assert sha(member)==rec['sha256_member_gzip'];raw=gzip.decompress(member);assert sha(raw)==rec['sha256_registro_jsonl'];proof=json.loads(raw);r=proof['registro'];assert r==public[r['path']];md=proof['md_final_utf8'].encode();htmlraw=base64.b64decode(proof['html_original_base64'],validate=True);api_raw=proof['metadados_raw'].encode();assert sha(md)==r['sha256_candidato']==rec['sha256_md_final'];assert sha(htmlraw)==r['sha256_html']==rec['sha256_html'];assert sha(api_raw)==r['sha256_metadados']==rec['sha256_metadados'];meta,_,body=fields(md.decode());api=json.loads(api_raw);assert meta['urn']==r['urn']==api['legislationIdentifier'];assert meta['data']==r['data']==api['legislationDate'];assert api['legislationType'] in {'Decreto','Decreto Numerado'};assert meta['sha256_metadados_fonte']==sha(api_raw);assert meta['numero']==r['numero'];m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(\d+)-(\d{4}-\d\d-\d\d).md',r['path']);assert m and m[3]==r['data'] and str(int(m[2]))==r['numero'];identity=(r['numero'].lstrip('0'),m[1]);assert r['path'] not in paths and r['urn'] not in urns and identity not in identities and identity not in known;paths.add(r['path']);urns.add(r['urn']);identities.add(identity)
 enc=f.escolher_texto(api);assert enc==r['fontes']['encoding_escolhido'];assert enc['contentUrl'].replace('/api/binario/','/api/public/binario/')==r['fontes']['texto']['url'];assert r['fontes']['texto']['sha256_raw']==sha(htmlraw) and r['fontes']['metadados']['sha256_raw']==sha(api_raw);assert (ROOT/r['candidato']).read_bytes()==md; text=htmlraw.decode('utf-8');converted=f.convert(text);ep=extrair_epigrafe_decreto(converted);assert ep==r['epigrafe'] and ep['data']==r['data'] and ep['numero']==numero_normalizado(meta['numero']);assert not f.motivo_texto_parcial_decreto('DEC-n',converted);sp=Visivel();sp.feed(text);assert not sp.visual and not anexo_proprio_ausente(converted,sp);closings,boundary=closing_env['principal_fechos'](converted);assert len(closings)==1 and closings[0]==r['fecho_principal'] and closings[0]['data']==r['data'];norm,admin=normalizar_marcador_administrativo(text,{'urn':r['urn'],'epigrafe':r['epigrafe']});assert norm==proof['HTML_normativo_normalizado'] and admin==proof['normalizacao_administrativa'];title,sep,payload=body.lstrip().partition('\n');assert title.startswith('# Decreto ') and sep
 if r['representacao']=='HTML normativo integral':
  inner=re.search(r'<body\b[^>]*>([\s\S]*?)</body\s*>',norm,re.I);assert inner;expected='<div>\n'+inner[1].strip()+'\n</div>\n';assert payload.strip()==expected.strip();assert proof['reparo_nativo']['replay']['aprovado'] is True
 else:assert payload.strip()==converted.strip() and proof['replay_basico']['aprovado'] and proof['replay_HTML5']['aprovado']
 note=proof['nota_editorial']
 if note:
  assert sha(body.encode())==note['sha256_corpo_inalterado'];line=re.compile(r'^'+re.escape(note['campo_editorial'])+r': .*\n',re.M);assert len(line.findall(md.decode()))==1;without=line.sub('',md.decode());assert sha(without.encode())==note['predecessor_privado']['sha256']
 rows.append({'path':r['path'],'markdown':payload,'norm':norm})
for part in mapping['partes']:assert positions[part['path']]==part['bytes_gzip'] and counts[part['path']]==part['registros']
assert paths==set(public);code="import {marked} from '/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));";marked={r['path']:r['html'] for r in json.loads(subprocess.check_output(['node','--input-type=module','-e',code],input=json.dumps(rows).encode()))};cm=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False})
for r in rows:
 a=v.texto_visivel_html(r['norm']);sp=Visivel();sp.feed(r['norm']);st=html5lib.parse(r['norm'],treebuilder='etree',namespaceHTMLElements=False);a5=env['visible'](st.find('body'));sm=env['matrices'](st);sl=env['lists'](st)
 for h in [marked[r['path']],cm.render(r['markdown'])]:
  b=v.texto_visivel_html(h);mp=Visivel();mp.feed(h);rt=html5lib.parse(h,treebuilder='etree',namespaceHTMLElements=False);b5=env['visible'](rt.find('body'));assert a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and sp.structure==mp.structure and not mp.visual and a5==b5 and v.assinatura_numerica(a5)==v.assinatura_numerica(b5) and contexto_numerico(a5)==contexto_numerico(b5) and sm==env['matrices'](rt) and sl==env['lists'](rt),r['path']
print('Replay portátil: fontes/CRC/MD/identidade/fecho principal/baseline e dois motores+HTML5 aprovados em',len(rows),'documentos; zero escrita ou rede.')
