"""Reconstitui o replay de 3.848 corpos exclusivamente dos insumos da entrega.

Não lê caches normativos nem escreve destinos canônicos. Produz saídas em nova
pasta persistente de auditoria; executa somente o renderizador Markdown local.
"""
from pathlib import Path
import json,gzip,hashlib,subprocess,sys,datetime,ast
D=Path(__file__).resolve().parent;ROOT=D.parents[4];sha=lambda b:hashlib.sha256(b).hexdigest();sys.path.insert(0,str(ROOT/'scripts'));from preparar_lote_decretos_cache import fields
hashes=json.loads((D/'entrega3848-artefatos-hashes.json').read_text())['arquivos'];expected={r['path']:r['sha256'] for r in hashes}
for rel in [str((D/'resultado.json').relative_to(ROOT)),str((D/'validar.py').relative_to(ROOT)),str((D/'verificacao3848.json').relative_to(ROOT)),'federal/_fonte/auditorias/retomada_federal_20261027_003/render_estrutural_v2.mjs','federal/_provas_commonmark_cumulativo015018_20261021_001/commonmark-listas-helper.py.txt']:
 assert sha((ROOT/rel).read_bytes())==expected[rel],rel
mp=D/'fontes3848/mapa_fontes3848.json';assert sha(mp.read_bytes())==expected[str(mp.relative_to(ROOT))];m=json.loads(mp.read_text());archive={}
for part in m['partes']:
 p=ROOT/part['path'];assert sha(p.read_bytes())==part['sha256_gzip']
 with gzip.open(p,'rt') as f:
  for line in f:
   r=json.loads(line);assert r['path'] not in archive
   for key,h in [('md_final','sha256_md_final'),('html_original','sha256_html'),('metadados_raw','sha256_metadados')]:assert sha(r[key].encode())==r[h]
   api=json.loads(r['metadados_raw']);assert api['legislationDate']==r['data'] and api['legislationIdentifier']==r['urn'];archive[r['path']]=r
assert len(archive)==3848;verification=json.loads((D/'verificacao3848.json').read_text());oldqa={r['path']:r for r in json.loads((D/'resultado.json').read_text())['registros']};rows=[]
for r in verification['registros']:
 a=archive[r['path']];q=oldqa[r['path']];assert a['sha256_md_final']==r['sha256_md_final']==q['sha256_md_final'] and a['sha256_html']==r['sha256_html'];proof={'fonte_html_cache':r['fonte_html_cache'],'sha256_fonte_html':r['sha256_html'],'marcador_administrativo_excluido':{'paragrafos':q['administrativos_excluidos']} if q['administrativos_excluidos'] else None,'normalizacoes_apresentacao':q['normalizacoes_apresentacao']};rows.append(dict(r,sha256=r['sha256_md_final'],sha256_fonte_html=r['sha256_html'],epigrafe={'numero':r['numero'],'data':r['data']},proof=proof,HTML_original=q['HTML_original']))
work=D/('replay_runtime_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));work.mkdir(exist_ok=False);(work/'preparo.json').write_text(json.dumps({'publicaveis':rows}));(work/'render_input.json').write_text(json.dumps([{'path':p,'markdown':fields(r['md_final'])[2].lstrip().partition('\n')[2]} for p,r in archive.items()]));renderer=ROOT/'federal/_fonte/auditorias/retomada_federal_20261027_003/render_estrutural_v2.mjs';subprocess.run(['node',str(renderer),str(work/'render_input.json'),str(work/'render_output.json')],check=True)
source=(D/'validar.py').read_text();source=source.replace('BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4]','BASE=RUNTIME;ROOT=REPO_ROOT');needle="src=gzip.decompress((ROOT/pr['fonte_html_cache']).read_bytes()).decode()";assert needle in source;source=source.replace(needle,"src=ARCHIVE[r['path']]['html_original']");needle="raw=(ROOT/r['arquivo_final']).read_bytes()";assert needle in source;source=source.replace(needle,"raw=ARCHIVE[r['path']]['md_final'].encode()");ast.parse(source);(work/'validar_io_reconstituido.py').write_text(source);exec(compile(source,str(work/'validar_io_reconstituido.py'),'exec'),{'__file__':str(work/'validar_io_reconstituido.py'),'RUNTIME':work,'REPO_ROOT':ROOT,'ARCHIVE':archive});result=json.loads((work/'resultado.json').read_text());assert result['resumo']=={'auditados':3848,'aprovados':3848,'divergencias':0};print('Replay concluído:',work)
