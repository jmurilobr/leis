from pathlib import Path
import sys,json,gzip,hashlib,subprocess,re,os,tempfile
sha=lambda b:hashlib.sha256(b).hexdigest()
def durable_new(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
def replace_exact(path,new,old):
 assert not path.is_symlink() and path.read_bytes()==old,'preimagem divergente'
 fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.root18351-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out:out.write(new);out.flush();os.fsync(out.fileno())
  os.chmod(tmp,path.stat().st_mode & 0o777)
  assert not path.is_symlink() and path.read_bytes()==old,'preimagem mudou';os.replace(tmp,path);assert path.read_bytes()==new
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def main():
 root=Path.cwd().resolve();sys.path.insert(0,str(root/'scripts'));from preparar_lote_decretos_cache import fields
 head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();h={}
 def add(path,digest=None):
  p=Path(path);assert not p.is_absolute() and '..' not in p.parts and p.resolve()==root/p
  d=sha(p.read_bytes());assert digest is None or d==digest,str(p)
  if str(p) in h:assert h[str(p)]==d
  h[str(p)]=d
 for name,prefix in [('clbr_recuperacoes1945_20261028_001','entrega18351'),('clbr_recuperacoes1945_20261028_002','entrega')]:
  B=Path('federal/_fonte/auditorias')/name;lp=B/(prefix+'-paths.txt');hp=B/(prefix+'-hashes.json');o=json.loads(hp.read_bytes());rows=o if isinstance(o,list) else o['arquivos'];listed=lp.read_text().splitlines();assert len(listed)==len(set(listed));assert {r['path'] for r in rows} in [set(listed),set(listed)|{str(lp)}]
  if isinstance(o,dict):assert sha(lp.read_bytes())==o['sha256_lista']
  for r in rows:add(r['path'],r['sha256']);assert Path(r['path']).stat().st_size==r['bytes']
  add(lp);add(hp)
 B=Path('federal/_fonte/auditorias/revisao_independente18351_vigencia_20261028');mp=B/'manifesto.json';assert sha(mp.read_bytes())=='29077b62a2aa34a69e46c3beee67a4d177ba08b7a15958ca03e219fefa252676'
 for r in json.loads(mp.read_bytes())['arquivos']:add(r['path'],r['sha256']);assert Path(r['path']).stat().st_size==r['bytes']
 add(mp);add(B/'paths.txt')
 mp=Path('federal/_fonte/auditorias/clbr_recuperacoes1945_20261028_002/candidato18351.json');m=json.loads(mp.read_bytes());p=Path(m['path_canonico']);assert str(p)=='federal/decretos/1945/dec-18351-1945-04-11.md';old=p.read_bytes();assert sha(old)==m['preimagem']['sha256']=='824478dedd2f5029b7bc5cf5d06afbf35ab509639e9b9de874862cab82a0feef';assert Path(m['preimagem']['path']).read_bytes()==old==subprocess.check_output(['git','show',head+':'+str(p)])
 new=Path(m['candidato']['path']).read_bytes();assert sha(new)==m['candidato']['sha256']=='5bda4405badffde35f70a703bb214e3f229beec3423d965c5253801476c77144';om,_,ob=fields(old.decode());nm,_,nb=fields(new.decode())
 for k in ['titulo','tipo','numero','data','ementa','revogada','forca_legal_fonte','fonte_metadados','sha256_metadados_fonte','urn']:assert om[k]==nm[k],k
 assert nm['versao_texto']=='edição CLBR original integral em fac-símile' and nm['baixado_em']=='2026-10-27' and nm['fonte_texto_anterior']==om['fonte'];pdf=m['fonte_PDF_anual'];assert nm['sha256_pdf_fonte']==pdf['sha256'];add(pdf['path'],pdf['sha256']);assert Path(pdf['path']).stat().st_size==pdf['bytes']<95*1024**2;add(m['recibo_captura']['path'],m['recibo_captura']['sha256'])
 links=re.findall(r'!\[[^\n]*\]\(([^)]+)\)',nb);assets=m['ativos_em_ordem_impressa'];assert len(links)==len(assets)==22;assert [a['pagina_impressa'] for a in assets]==list(range(132,154));targets=[]
 proofpath=Path('federal/_fonte/auditorias/recuperacao18351-ROOT-render-20261028/recibo.json');render=json.loads(proofpath.read_bytes());assert render['aprovados']==22 and render['fonte']==pdf;add(proofpath)
 for a,link,proof in zip(assets,links,render['ativos']):
  source=Path(a['path']);target=Path(a['destino']);assert str(target).startswith('federal/anexos/decretos/1945/dec-18351-1945-04-11-clbr-p') and not target.is_absolute() and '..' not in target.parts;assert (p.parent/link).resolve()==target.resolve()==root/target;assert not target.exists() and not target.is_symlink();assert sha(source.read_bytes())==a['sha256']==proof['sha256_ativo'];assert proof['ativo']==str(source) and proof['igualdade_pixels'] is True;targets.append(str(target))
 assert len(set(targets))==22;check=subprocess.check_output(['git','cat-file','--batch-check'],input=''.join(head+':'+x+'\n' for x in targets).encode()).splitlines();assert len(check)==22 and all(x.endswith(b' missing') for x in check)
 rp=Path('scripts/dados/pendencias-integralidade-publicadas.json');oldreg=rp.read_bytes();assert subprocess.check_output(['git','show',head+':'+str(rp)])==oldreg;reg=json.loads(oldreg);assert not any(r['path']==str(p) for r in reg['pendentes']);assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head
 print('ROOT18351: preimagem, identidade, edição CLBR1945IV, captura27/10, 22 folhas, pixels independentes e links aprovados; registro de pendências sem alteração, zero normas novas.',flush=True)
 if '--apply' not in sys.argv:return
 C=Path('federal/_fonte/auditorias/recuperacao18351-ROOT-20261028');C.mkdir(exist_ok=False)
 for name,raw in [('preimagem.md.gz',gzip.compress(old,mtime=0)),('candidato.md.gz',gzip.compress(new,mtime=0))]:durable_new(C/name,raw);add(C/name)
 intent={'HEAD':head,'sha256_preimagem':sha(old),'sha256_candidato':sha(new),'assets':assets,'pendencias_inalteradas_sha256':sha(oldreg),'criterio':'ROOT viu todas as 22 folhas, capa, índice XIV, primeira página integral e limite154. Mesmo corpo e figuras da edição CLBR, sem mesclar a anterior. Suboficiais preservado no Art1; rótulo neutro da página152 não emenda fonte. Sem inferência de vigência.','sha256_recibo_render':sha(proofpath.read_bytes())};durable_new(C/'intencao.json',(json.dumps(intent,ensure_ascii=False,indent=2)+'\n').encode());add(C/'intencao.json')
 for a in assets:
  assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head;target=Path(a['destino']);assert target.resolve()==root/target;raw=Path(a['path']).read_bytes();assert sha(raw)==a['sha256'];durable_new(target,raw);add(target,a['sha256'])
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head and rp.read_bytes()==oldreg;replace_exact(p,new,old);add(p)
 durable_new(C/'resultado.json',(json.dumps({'HEAD':head,'recuperados':1,'novas_normas':0,'registro_pendencias_inalterado':True,'sha256':h},ensure_ascii=False,indent=2)+'\n').encode());add(C/'resultado.json');Path('_fonte/operacao_root_20261027/recuperacao18351-hashes.json').write_text(json.dumps(h,ensure_ascii=False,indent=2)+'\n');print('ROOT18351 aplicado, 22 ativos, preimagem preservada, zero normas novas',flush=True)
if __name__=='__main__':main()
