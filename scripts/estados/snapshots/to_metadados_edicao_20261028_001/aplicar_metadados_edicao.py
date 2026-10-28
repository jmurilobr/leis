"""Overlay de edição TO, privado; dry-run padrão e apply exclusivo ROOT.

Altera apenas versao_texto/edicao/observacao_edicao. Corpo inteiro, incluindo H1,
permanece byte idêntico. Aplicar grupo186 somente após a promoção desse lote.
"""
from pathlib import Path
import argparse,json,hashlib,os,tempfile,datetime,shutil,subprocess
SHA=lambda b:hashlib.sha256(b).hexdigest()
ALLOWED={'versao_texto','edicao','observacao_edicao'}
def read(blob):
 if not blob.startswith(b'---\n'):raise ValueError('cabeçalho não reconhecido')
 h,b=blob[4:].split(b'\n---\n',1);lines=h.decode('utf-8').splitlines();meta={}
 for line in lines:
  k,v=line.split(': ',1)
  if k in meta:raise ValueError('campo repetido')
  meta[k]=json.loads(v)
 return meta,b,lines

def rewrite(blob,values):
 old,body,lines=read(blob)
 if set(values)!=ALLOWED or 'observacao_edicao' in old:raise ValueError('escopo de metadados divergente')
 changed=[]
 for line in lines:
  key=line.split(': ',1)[0];changed.append(key+': '+json.dumps(values[key],ensure_ascii=False) if key in values else line)
 changed.append('observacao_edicao: '+json.dumps(values['observacao_edicao'],ensure_ascii=False));new=b'---\n'+('\n'.join(changed)+'\n').encode()+b'---\n'+body
 verify(blob,new,values);return new

def verify(old,new,values):
 a,bodya,_=read(old);b,bodyb,_=read(new)
 if bodya!=bodyb:raise ValueError('corpo/H1 alterado')
 if set(b)-set(a)!={'observacao_edicao'} or set(a)-set(b):raise ValueError('chaves fora do escopo')
 if list(b)!=list(a)+['observacao_edicao']:raise ValueError('ordem de campos alterada')
 for k,v in a.items():
  if k not in ALLOWED and b[k]!=v:raise ValueError('campo protegido alterado: '+k)
 if any(b.get(k)!=v for k,v in values.items()):raise ValueError('valor proposto diverge')
 return True

def safe(root,p):
 p=Path(p)
 if p.is_absolute() or '..' in p.parts or not (root/p).resolve().is_relative_to(root):raise ValueError('caminho relativo inseguro')
 return root/p

def save(p,data):
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifesto',required=True);ap.add_argument('--hashes',required=True);ap.add_argument('--controle',required=True);ap.add_argument('--grupo',choices=['45','178','186','todos'],default='todos');ap.add_argument('--apply',action='store_true');ap.add_argument('--confirmar-root',choices=['ROOT']);a=ap.parse_args()
 if a.apply and a.confirmar_root!='ROOT':ap.error('--apply é exclusivo ROOT')
 root=Path.cwd().resolve();device=root.stat().st_dev
 if not (root/'.git').exists():raise ValueError('repositório/volume indisponível')
 mp=safe(root,a.manifesto);hp=safe(root,a.hashes);maps=json.loads(hp.read_text());m=json.loads(mp.read_text())
 if maps.get(a.manifesto)!=SHA(mp.read_bytes()):raise ValueError('manifesto fora do mapa')
 for p,sha in maps.items():
  if SHA(safe(root,p).read_bytes())!=sha:raise ValueError('SHA divergente: '+p)
 docs=[r for r in m['documentos'] if a.grupo=='todos' or r['grupo']==a.grupo];ready=[];absent=[]
 for r in docs:
  old=safe(root,r['preimagem']).read_bytes();new=safe(root,r['privado']).read_bytes()
  if SHA(old)!=r['sha256_preimagem'] or SHA(new)!=r['sha256_proposta']:raise ValueError('preimagem/proposta divergente')
  verify(old,new,r['metadados_propostos']);dest=safe(root,r['path'])
  if not os.path.lexists(dest):absent.append(r['path']);continue
  if dest.is_symlink() or SHA(dest.read_bytes())!=r['sha256_preimagem']:raise ValueError('canônico divergiu da preimagem: '+r['path'])
  ready.append(r)
 control=safe(root,a.controle)
 if not str(control.relative_to(root)).startswith('estaduais/TO/_fonte/auditorias/'):raise ValueError('controle fora do espaço privado TO')
 control.mkdir(parents=True,exist_ok=False);head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();save(control/'intencao.json',dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),HEAD=head,grupo=a.grupo,modo='apply_ROOT' if a.apply else 'dry-run',prontos=len(ready),aguardando_promocao=absent,documentos=docs,sem_Git_escrita=True))
 if a.apply:
  if absent:raise ValueError('aguardar promoção dos destinos ausentes')
  for r in ready:
   backup=control/'backup'/r['path'];backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(root,r['path']),backup)
   if SHA(backup.read_bytes())!=r['sha256_preimagem']:raise ValueError('backup diverge')
  with (control/'journal.jsonl').open('x') as journal:
   for r in ready:
    if root.stat().st_dev!=device or not (root/'.git').exists() or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=head:raise ValueError('volume/HEAD mudou')
    dest=safe(root,r['path'])
    if SHA(dest.read_bytes())!=r['sha256_preimagem']:raise ValueError('canônico mudou antes da troca')
    fd,tmp=tempfile.mkstemp(prefix='.to-metadados-',dir=dest.parent)
    try:
     with os.fdopen(fd,'wb') as f:f.write(safe(root,r['privado']).read_bytes());f.flush();os.fsync(f.fileno())
     os.chmod(tmp,dest.stat().st_mode & 0o777);os.replace(tmp,dest)
    finally:
     if os.path.exists(tmp):os.unlink(tmp)
    journal.write(json.dumps(dict(path=r['path'],sha256=SHA(dest.read_bytes())),ensure_ascii=False)+'\n');journal.flush();os.fsync(journal.fileno())
 result=dict(finalizado_em=datetime.datetime.now().astimezone().isoformat(),modo='apply_ROOT' if a.apply else 'dry-run',prontos=len(ready),aguardando_promocao=absent,alterados=len(ready) if a.apply else 0,sem_Git_escrita=True);save(control/'resultado.json',result);print(json.dumps(result))
if __name__=='__main__':main()
