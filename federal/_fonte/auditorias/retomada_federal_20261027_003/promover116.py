"""ROOT only: validate every input first; default performs no writes.

Use --apply only after reviewing this program and its frozen receipt. No Git writes,
network, converter or metadata edits. Archived final bytes are the only promoted bytes.
"""
import sys
sys.dont_write_bytecode=True
import argparse,json,gzip,hashlib,re,os,datetime,subprocess
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];PACK=BASE.parent/'retomada_federal_20261027_002';sha=lambda b:hashlib.sha256(b).hexdigest()
def read_json(path):return json.loads(path.read_bytes())
def safe(path):
 p=(ROOT/path).resolve();assert p.is_relative_to(ROOT) and '..' not in Path(path).parts;return p
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args();receipt=read_json(BASE/'recibo_promocao116.json')
for r in receipt['insumos']:
 p=safe(r['path']);assert sha(p.read_bytes())==r['sha256'],r['path']
assert sha(Path(__file__).read_bytes())==receipt['sha256_runner']
verified=read_json(PACK/'verificacao_3608.json');vs={r['path']:r for r in verified['registros']};assert len(vs)==3608
prom=read_json(PACK/'promocoes_116.json')['substituicoes'];ps={r['path']:r for r in prom};assert len(ps)==116
package=read_json(PACK/'fontes3608/mapa_fontes3608.json');assert len(package['registros'])==3608
for r in read_json(PACK/'publicar3608-hashes.json')['arquivos']:assert sha(safe(r['path']).read_bytes())==r['sha256'],r['path']
for r in package['partes']:
 p=safe(r['path']);assert p.stat().st_size==r['bytes_gzip'] and p.stat().st_size<95*1024**2;assert sha(p.read_bytes())==r['sha256_gzip']
seen=set();urns=set();identities=set();pending=[];states={}
for r in package['registros']:
 path=r['path'];assert path in vs and path not in seen and re.fullmatch(r'federal/decretos/\d{4}/dec-[^/]+\.md',path);seen.add(path);v=vs[path]
 with safe(r['arquivo']).open('rb') as f:f.seek(r['offset_gzip']);member=f.read(r['bytes_gzip_member'])
 assert sha(member)==r['sha256_member_gzip'];raw=gzip.decompress(member);assert sha(raw)==r['sha256_registro_jsonl'];obj=json.loads(raw);assert obj['path']==path and obj['urn']==v['urn'];assert obj['urn'] not in urns;urns.add(obj['urn']);key=(obj['numero'],obj['data'][:4]);assert key not in identities;identities.add(key)
 for field,hkey in [('md_final','sha256_md_final'),('html_original','sha256_html'),('metadados_raw','sha256_metadados')]:assert sha(obj[field].encode())==obj[hkey]==r[hkey]==v[hkey]
 meta=json.loads(obj['metadados_raw']);assert meta['legislationIdentifier']==obj['urn'] and meta['legislationDate']==obj['data'] and meta['legislationType'] in {'Decreto Numerado','Decreto'}
 final=obj['md_final'].encode();assert sha(safe(v['arquivo_final']).read_bytes())==v['sha256_md_final'];current=safe(path).read_bytes();ch=sha(current)
 if path in ps:
  p=ps[path];before=obj['md_preimagem'].encode();assert sha(before)==obj['sha256_preimagem']==r['sha256_preimagem']==p['sha256_preimagem'];assert sha(final)==p['sha256_candidato'];assert ch in {p['sha256_preimagem'],p['sha256_candidato']},path
  states[path]='preimagem' if ch==p['sha256_preimagem'] else 'já promovido';pending.append({'path':path,'before':before,'final':final,'skip':ch==p['sha256_candidato']})
 else:assert obj['md_preimagem'] is None and ch==obj['sha256_md_final'],path
assert len(seen)==3608 and len(pending)==116
replay=read_json(BASE/'replay3608_cumulativo.json');assert replay['resumo']=={'auditados':3608,'aprovados':3608,'divergencias':0};assert all(r['aprovado'] and r['sha256_md_final']==vs[r['path']]['sha256_md_final'] for r in replay['registros'])
github=read_json(BASE/'github_dois/resultado.json');assert github['resumo']=={'chamadas':2,'aprovados':2,'divergencias':0}
for r in github['registros']:
 assert r['aprovado'] and r['sha256_md_final']==vs[r['path']]['sha256_md_final']
 for field in ['request','response']:assert sha(safe(r[field]['path']).read_bytes())==r[field]['sha256']
q=subprocess.run(['git','cat-file','--batch-check'],cwd=ROOT,input=''.join('HEAD:'+p+'\n' for p in sorted(seen)),text=True,capture_output=True,check=True);assert len(q.stdout.splitlines())==3608 and all(l.endswith(' missing') for l in q.stdout.splitlines()),'Um destino já consta de HEAD; revisar antes de promover.'
# Additional current-HEAD check by number/year, scoped to the selected years.
years=sorted({v['data'][:4] for v in vs.values()})
tree=subprocess.check_output(['git','ls-tree','-rz','HEAD','--']+['federal/decretos/'+y for y in years],cwd=ROOT)
def number_key(value):return re.sub(r'[.\s]','',value).upper().lstrip('0') or '0'
selected={(number_key(v['numero']),v['data'][:4]) for v in vs.values()}
for entry in tree.split(b'\0'):
 if not entry:continue
 path=entry.split(b'\t',1)[1].decode();match=re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md',path)
 if match:assert (number_key(match[2]),match[1]) not in selected,('Colisão número/ano em HEAD',path)
print('Validação integral concluída: 3.608 fontes/candidatos e 116 preimagens; nenhuma escrita realizada.',flush=True)
if not args.apply:raise SystemExit(0)
# All validation above completes before this first write, including backups/logs.
D=BASE/('promocao_ROOT_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));D.mkdir(exist_ok=False)
intent=[]
for i,r in enumerate(pending,1):
 p=D/(f'{i:03}_'+Path(r['path']).name+'.preimagem');p.write_bytes(r['before']);assert sha(p.read_bytes())==ps[r['path']]['sha256_preimagem'];intent.append({'path':r['path'],'backup':str(p.relative_to(ROOT)),'sha256_preimagem':sha(r['before']),'sha256_final':sha(r['final']),'ja_promovido':r['skip']})
(D/'intencao.json').write_text(json.dumps(intent,ensure_ascii=False,indent=2)+'\n')
log=D/'aplicacao.jsonl'
for r in pending:
 target=safe(r['path']);expected=ps[r['path']]['sha256_candidato'] if r['skip'] else ps[r['path']]['sha256_preimagem'];assert sha(target.read_bytes())==expected,r['path']
 if not r['skip']:
  temp=target.with_name('.'+target.name+'.promocao116.tmp');assert not temp.exists()
  with temp.open('xb') as f:f.write(r['final']);f.flush();os.fsync(f.fileno())
  os.replace(temp,target)
 assert sha(target.read_bytes())==ps[r['path']]['sha256_candidato']
 with log.open('a') as f:f.write(json.dumps({'path':r['path'],'sha256_final':sha(r['final']),'estado':'já promovido' if r['skip'] else 'promovido'},ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
assert all(sha(safe(r['path']).read_bytes())==ps[r['path']]['sha256_candidato'] for r in pending)
print('ROOT: 116 destinos finais conferidos; nenhuma operação Git. Recibo:',D,flush=True)
