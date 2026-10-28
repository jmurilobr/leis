from pathlib import Path
import json,hashlib,gzip,subprocess,os,tempfile
sha=lambda b:hashlib.sha256(b).hexdigest();h={}
def add(p,s=None):
 p=Path(p);d=sha(p.read_bytes());assert s is None or s==d,str(p)
 if str(p) in h:assert h[str(p)]==d
 h[str(p)]=d
for name in ['guard_bibliografico_20261027_004','guard_bibliografico_20261028_005']:
 B=Path('federal/_fonte/auditorias')/name;l=B/'entrega-paths.txt';q=B/'entrega-hashes.json';o=json.loads(q.read_bytes());rows=o if isinstance(o,list) else o['arquivos'];assert {r['path'] for r in rows} in [set(l.read_text().splitlines()),set(l.read_text().splitlines())|{str(l)}]
 if isinstance(o,dict):assert sha(l.read_bytes())==o['sha256_lista']
 for r in rows:add(r['path'],r['sha256'])
 add(l);add(q)
p=Path('scripts/integridade_anexos_decreto.py');old=p.read_bytes();assert not p.is_symlink() and sha(old)=='3cd60ac4a398a27cc0f646f891e853f6b120b1a963deb4cc9f0ccfd7d6ca0cd0';head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert head=='80e3577a4941abd17fc28cdd26f79a157de03152';assert subprocess.check_output(['git','show',head+':'+str(p)])==old
q=Path('federal/_fonte/auditorias/guard_bibliografico_20261028_005/integridade_anexos_decreto.py');new=q.read_bytes();assert sha(new)=='e7acf0ce9ada5bb7d0e062dd20afd66724fef43109328046ef519a6e8a23abac';compile(new,str(p),'exec')
target=Path('scripts/test_guard_bibliografico_20261028.py');assert not os.path.lexists(target);test=Path('_fonte/operacao_root_20261027/test_guard_bibliografico_20261028.py').read_bytes();compile(test,str(target),'exec')
delta=json.loads(Path('_fonte/operacao_root_20261027/guard87-delta3896-root.json').read_bytes());assert delta['fontes_examinadas']==3896 and delta['mudancas_de_estado']==2 and delta['mudancas_nos_selecionados013_015']==0;assert all(r['estado_HEAD']=='ausente' and not r['selecionado_lotes013_015'] for r in delta['registros'])
paths=[r['path'] for r in delta['registros']];assert {x.split('/dec-')[1].split('-')[0] for x in paths}=={'14056','14722'};missing=subprocess.check_output(['git','cat-file','--batch-check'],input=''.join(head+':'+x+'\n' for x in paths).encode()).splitlines();assert len(missing)==2 and all(x.endswith(b' missing') for x in missing)
C=Path('federal/_fonte/auditorias/guard87-ROOT-20261028');C.mkdir(exist_ok=False)
def durable(path,raw):
 with path.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
durable(C/'guard74-preimagem.py.gz',gzip.compress(old,mtime=0));add(C/'guard74-preimagem.py.gz');durable(C/'guard87-candidato.py.gz',gzip.compress(new,mtime=0));add(C/'guard87-candidato.py.gz')
durable(C/'intencao.json',(json.dumps({'HEAD':head,'sha256_guard74':sha(old),'sha256_guard87':sha(new),'teste_novo':str(target),'sha256_teste':sha(test),'delta3896':delta,'criterio':'ROOT repetiu 87 testes e o delta de 3.896 fontes antes de integrar. Dois casos de 015 já estavam retidos; nenhum selecionado mudou. Normas 016 permanece apenas selecionado offline; imports independentes do DOU verificados por leitura. Nenhuma norma ou registro de pendências alterado. Legado 74 e replays 439/411 publicados no commit 80e357.'},ensure_ascii=False,indent=2)+'\n').encode());add(C/'intencao.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head and p.read_bytes()==old
fd,tmp=tempfile.mkstemp(prefix='.guard87-',dir=p.parent)
with os.fdopen(fd,'wb') as out:out.write(new);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==old;os.chmod(tmp,p.stat().st_mode & 0o777);os.replace(tmp,p);add(p,sha(new))
fd,tmp=tempfile.mkstemp(prefix='.test-guard87-',dir=target.parent)
with os.fdopen(fd,'wb') as out:out.write(test);out.flush();os.fsync(out.fileno())
os.chmod(tmp,0o644);os.link(tmp,target);os.unlink(tmp);add(target,sha(test))
durable(C/'resultado.json',(json.dumps({'HEAD':head,'guard_integrado':sha(new),'teste_novo':str(target),'normas_alteradas':0,'registro_alterado':False,'sha256':h},ensure_ascii=False,indent=2)+'\n').encode());add(C/'resultado.json');Path('_fonte/operacao_root_20261027/guard87-publicar-hashes.json').write_text(json.dumps(h,ensure_ascii=False,indent=2)+'\n');print('Guard87integrado,13regressõescanônicasnovas;normas/registrointactos')
