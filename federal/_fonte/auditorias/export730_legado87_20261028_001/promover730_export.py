"""ROOT: replay integral portátil + dedup atual; --apply exclusivo ROOT."""
from pathlib import Path
import sys,argparse,json,gzip,hashlib,re,subprocess,os,datetime
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;ROOT=B.parents[3].resolve();sha=lambda b:hashlib.sha256(b).hexdigest()
def safe(p):
 p=Path(p);assert not p.is_absolute() and '..' not in p.parts;joined=ROOT/p;resolved=joined.resolve();assert resolved.is_relative_to(ROOT) and resolved==joined;return resolved
def key(n):return re.sub(r'[.\s]','',str(n)).upper().lstrip('0') or '0'
def syncdir(p):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def durable(p,raw):
 with p.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
a=argparse.ArgumentParser(description=__doc__);a.add_argument('--apply',action='store_true');args=a.parse_args();export=json.loads((B/'recibo_exportacao.json').read_bytes());assert sha(Path(__file__).read_bytes())==export['sha256_promotor_exportado'];assert sha((B/'versoes_exportadas.py').read_bytes())==export['sha256_resolvedor'];assert sha((B/'mapa_versoes.json').read_bytes())==export['sha256_mapa_versoes'];from versoes_exportadas import arquivo_logico,validar_export;validar_export();receipt=json.loads((B/'original_recibo_promocao730.json').read_bytes());assert sha((B/'original_promover730.py').read_bytes())==receipt['sha256_runner']
for r in receipt['insumos']:assert sha(arquivo_logico(r['path']).read_bytes())==r['sha256'],r['path']
subprocess.run([sys.executable,str(B/'replay730_export.py')],check=True,cwd=ROOT)
D=ROOT/'federal/_fonte/auditorias/alimentacao_normas_20261028_019/pacote_final001';manifest=json.loads((D/'lote_final.json').read_bytes());rows=manifest['publicaveis_privados'];assert len(rows)==730;prepared=[];paths=set();ids=set();urns=set();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
for r in rows:
 raw=safe(r['candidato']).read_bytes();assert sha(raw)==r['sha256_candidato'];assert not safe(r['path']).exists(),('Destino em disco',r['path']);m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(\d+)-(\d{4}-\d\d-\d\d)\.md',r['path']);assert m and m[3]==r['data'];ident=(key(m[2]),m[1]);assert ident not in ids and r['path'] not in paths and r['urn'] not in urns;ids.add(ident);paths.add(r['path']);urns.add(r['urn']);prepared.append({'path':r['path'],'candidato':r['candidato'],'raw':raw,'sha256':sha(raw)})
query=subprocess.run(['git','cat-file','--batch-check'],cwd=ROOT,input=''.join(head+':'+p+'\n' for p in sorted(paths)),text=True,capture_output=True,check=True);assert len(query.stdout.splitlines())==730 and all(x.endswith(' missing') for x in query.stdout.splitlines());years=sorted({y for n,y in ids});tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--']+['federal/decretos/'+y for y in years],cwd=ROOT)
for p in tree.decode().split('\0'):
 m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d\.md',p)
 if m:assert (key(m[2]),m[1]) not in ids,('Identidade já no HEAD',p)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head
print('730 validados integralmente, 19 retidos contextuais separados, ausentes por caminho e número/ano no HEAD '+head+'. Dry-run sem escrita.',flush=True)
if not args.apply:raise SystemExit(0)
A=B/('aplicacao_ROOT_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));A.mkdir(exist_ok=False);backups=[]
for i,r in enumerate(prepared,1):
 p=A/(f'{i:03}_'+Path(r['path']).name+'.candidato');durable(p,r['raw']);assert sha(p.read_bytes())==r['sha256'];backups.append({'path':r['path'],'candidato':r['candidato'],'backup':str(p.relative_to(ROOT)),'sha256_final':r['sha256'],'preimagem':'ausente'})
provenance=[D/'lote_final.json',D/'mapa_fontes.json',D/'baseline_decretos_anos.z.gz',arquivo_logico('federal/_fonte/auditorias/alimentacao_normas_20261028_019/qualificar_snapshot_v4.py'),B/'original_recibo730.json',B/'original_recibo_promocao730.json']+[safe(p['path']) for p in manifest['fontes_publicas_integrais']['partes']]
provenance += [B/'mapa_versoes.json',B/'recibo_exportacao.json',B/'versoes_exportadas.py',B/'replay730_export.py',B/'promover730_export.py']
for i,p in enumerate(provenance,1):durable(A/(f'fonte_{i:02}_'+p.name),p.read_bytes())
durable(A/'intencao.json',(json.dumps({'HEAD':head,'inclusoes':backups,'recibo':receipt},ensure_ascii=False,indent=2)+'\n').encode());syncdir(A)
for r in prepared:
 target=safe(r['path']);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name('.'+target.name+f'.promocao730.{os.getpid()}.tmp');durable(temp,r['raw']);assert sha(temp.read_bytes())==r['sha256'];os.link(temp,target);temp.unlink();syncdir(target.parent);assert sha(target.read_bytes())==r['sha256']
 with (A/'aplicacao.jsonl').open('a') as log:log.write(json.dumps({'path':r['path'],'sha256':r['sha256'],'estado':'criado atomicamente sem sobrescrever'},ensure_ascii=False)+'\n');log.flush();os.fsync(log.fileno())
assert all(sha(arquivo_logico(r['path']).read_bytes())==r['sha256'] for r in prepared);syncdir(A);print('ROOT: 730 inclusões conferidas; backups, fontes e intenção em',A,flush=True)
