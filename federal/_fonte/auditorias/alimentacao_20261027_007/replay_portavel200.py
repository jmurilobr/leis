"""Replay sem rede, cache transitório, conversão de fonte ou promoção."""
from pathlib import Path
import sys,json,gzip,hashlib,base64,subprocess,re
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-20261027/python'))
from markdown_it import MarkdownIt
from estados import pe_fidelidade_visivel as v
from auditar_pontuacao_federal import contexto_numerico
from integridade_html_federal import Visivel
from preparar_lote_decretos_cache import fields
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((B/'lote_camara200.json').read_bytes());p=ROOT/m['fontes_e_provas']['path'];assert sha(p.read_bytes())==m['fontes_e_provas']['sha256'];proofs=[json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()];assert len(proofs)==200;rows=[]
for x in proofs:
 assert sha(x['metadados_raw'].encode())==x['fila']['sha256_metadados_raw']
 for f in x['fontes_completas']:assert sha(base64.b64decode(f['bytes_originais_base64']))==f['recibo']['sha256_raw']
 if x['candidato_aprovado']:
  r=x['candidato_aprovado'];raw=x['md_final_utf8'].encode();assert sha(raw)==r['sha256_candidato'];meta,_,body=fields(raw.decode());assert meta['urn']==r['urn'];title,separator,body=body.lstrip().partition('\n');assert title.startswith('# Decreto ') and separator;rows.append({'path':r['path'],'markdown':body,'area':r['area_normativa_html']})
code="import {marked} from '/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));";render=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],input=json.dumps(rows).encode()));marked={r['path']:r['html'] for r in render};cm=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False})
for r in rows:
 a=v.texto_visivel_html(r['area']);sp=Visivel();sp.feed(r['area']);assert not sp.visual
 for html in [marked[r['path']],cm.render(r['markdown'])]:
  b=v.texto_visivel_html(html);mp=Visivel();mp.feed(html);assert a==b and v.assinatura_numerica(a)==v.assinatura_numerica(b) and contexto_numerico(a)==contexto_numerico(b) and sp.structure==mp.structure and not mp.visual and not re.search(r'<(?:ol|ul|li)\b',html,re.I),r['path']
assert len(rows)==m['resumo']['replay_aprovados'];print('Replay portátil: fontes 200 e candidatos',len(rows),'aprovados em marked 17 e CommonMark markdown-it-py 4, sem divergências ou escrita.')
