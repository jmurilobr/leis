from pathlib import Path
import sys,json,gzip,hashlib,subprocess,re,os,tempfile
sha=lambda b:hashlib.sha256(b).hexdigest()
def durable_new(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
def replace_exact(path,new,old):
 assert path.read_bytes()==old,'preimagem divergente'
 fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.root53480-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out:out.write(new);out.flush();os.fsync(out.fileno())
  assert path.read_bytes()==old,'preimagem mudou';os.replace(tmp,path);assert path.read_bytes()==new
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
 for name in ['recuperacao53480_facs_20261027_001','recuperacao53480_facs_20261028_002','recuperacao53480_facs_20261028_003']:
  B=Path('federal/_fonte/auditorias')/name;lp=B/'entrega-paths.txt';hp=B/'entrega-hashes.json';o=json.loads(hp.read_bytes());rows=o if isinstance(o,list) else o['arquivos'];listed=lp.read_text().splitlines();assert len(listed)==len(set(listed));assert {r['path'] for r in rows} in [set(listed),set(listed)|{str(lp)}]
  if isinstance(o,dict):assert sha(lp.read_bytes())==o['sha256_lista']
  for r in rows:add(r['path'],r['sha256'])
  add(lp);add(hp)
 B=Path('federal/_fonte/auditorias/recuperacao53480_facs_20261028_003');m=json.loads((B/'candidato53480.json').read_bytes());p=Path(m['path_canonico']);assert str(p)=='federal/decretos/1964/dec-53480-1964-01-23.md';old=p.read_bytes();assert sha(old)==m['preimagem']['sha256']=='60b9c427d89bf0df452e33e2ca802b71e0021ad695cb4f1dae364455577ddf2a';assert Path(m['preimagem']['path']).read_bytes()==old==subprocess.check_output(['git','show',head+':'+str(p)])
 new=Path(m['candidato']['path']).read_bytes();assert sha(new)==m['candidato']['sha256']=='9b8dabfe5617b48d653fab97928d9b6fa587239ec71740b6414d7b99ed2eac6f';om,_,ob=fields(old.decode());nm,_,nb=fields(new.decode())
 for k in ['titulo','tipo','numero','data','ementa','revogada','forca_legal_fonte','fonte_metadados','sha256_metadados_fonte','urn']:assert om[k]==nm[k],k
 assert nm['versao_texto']=='edição CLBR integral em fac-símile' and nm['baixado_em']=='2026-10-21' and nm['fonte_texto_anterior']==om['fonte'];assert nm['sha256_pdf_fonte']==m['fonte_primaria']['sha256'];add(m['fonte_primaria']['path'],m['fonte_primaria']['sha256']);assert Path(m['fonte_primaria']['path']).stat().st_size==m['fonte_primaria']['bytes']<95*1024**2
 links=re.findall(r'!\[[^\n]*\]\(([^)]+)\)',nb);assets=m['ativos_em_ordem_de_leitura'];assert len(links)==len(assets)==20;targets=[]
 proofpath=Path('federal/_fonte/auditorias/recuperacao53480-ROOT-render-20261028/recibo.json');render=json.loads(proofpath.read_bytes());assert render['aprovados']==20;add(proofpath)
 for a,link,proof in zip(assets,links,render['ativos']):
  source=Path(a['path']);target=Path(a['destino']);assert str(target).startswith('federal/anexos/decretos/1964/dec-53480-1964-01-23-') and not target.is_absolute() and '..' not in target.parts;assert (p.parent/link).resolve()==target.resolve();assert not target.exists() and not target.is_symlink();assert sha(source.read_bytes())==a['sha256']==proof['sha256_ativo'];assert proof['ativo']==str(source) and proof['igualdade_pixels'] is True;targets.append(str(target))
 assert len(set(targets))==20;check=subprocess.check_output(['git','cat-file','--batch-check'],input=''.join(head+':'+x+'\n' for x in targets).encode()).splitlines();assert len(check)==20 and all(x.endswith(b' missing') for x in check)
 rp=Path('scripts/dados/pendencias-integralidade-publicadas.json');oldreg=rp.read_bytes();assert subprocess.check_output(['git','show',head+':'+str(rp)])==oldreg;reg=json.loads(oldreg);removed=[r for r in reg['pendentes'] if r['path']==str(p)];assert len(reg['pendentes'])==7631 and len(removed)==1 and removed[0]['sha256_md']==sha(old)
 print('ROOT53480: identidade/metadados,ediçãoCLBR1964II,captura21/10,82artigos+9folhas/20imagens,render20pixeliguais e preimagemHEAD aprovados. 7631→7630; zero normas novas.',flush=True)
 if '--apply' not in sys.argv:return
 C=Path('federal/_fonte/auditorias/recuperacao53480-ROOT-20261028');C.mkdir(exist_ok=False)
 for name,raw in [('preimagem.md.gz',gzip.compress(old,mtime=0)),('pendencias7631.json.gz',gzip.compress(oldreg,mtime=0)),('candidato.md.gz',gzip.compress(new,mtime=0))]:durable_new(C/name,raw);add(C/name)
 intent={'HEAD':head,'sha256_preimagem':sha(old),'sha256_candidato':sha(new),'assets':assets,'remover_pendencia':removed,'criterio':'ROOTviu20imagens+capa/índicesIX/X/scanoriginal/crop600. Epígrafe53.480; notas antigas53.490 invalidadas por sucessores. CorpoArt1–82eassinaturas+modelos completos da mesma edição CLBR. Mapa7 identificado pela posição/título sem inventar rodapé. EdiçãoNormas anterior integral embackup; não mesclarcorpos e nãocertificarDOUretificação/vigência.','sha256_recibo_render':sha(proofpath.read_bytes())};durable_new(C/'intencao.json',(json.dumps(intent,ensure_ascii=False,indent=2)+'\n').encode());add(C/'intencao.json')
 for a in assets:
  assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head;target=Path(a['destino']);raw=Path(a['path']).read_bytes();assert sha(raw)==a['sha256'];durable_new(target,raw);add(target,a['sha256'])
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head;replace_exact(p,new,old);add(p)
 reg['pendentes']=[r for r in reg['pendentes'] if r['path']!=str(p)];assert len(reg['pendentes'])==7630;replace_exact(rp,(json.dumps(reg,ensure_ascii=False,indent=2)+'\n').encode(),oldreg);add(rp)
 durable_new(C/'resultado.json',(json.dumps({'HEAD':head,'recuperados':1,'novas_normas':0,'pendencias_antes':7631,'pendencias_depois':7630,'sha256':h},ensure_ascii=False,indent=2)+'\n').encode());add(C/'resultado.json');Path('_fonte/operacao_root_20261027/recuperacao53480-hashes.json').write_text(json.dumps(h,ensure_ascii=False,indent=2)+'\n');print('ROOT53480aplicado:preimagenspreservadas,20ativoscriados,registro7630,zero novasnormas',flush=True)
if __name__=='__main__':main()
