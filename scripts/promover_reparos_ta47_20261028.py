"""Promoção privada dos 46 escapes e fecho tachado de Buritis; somente ROOT aplica.

Dry-run padrão. Confere pacote congelado, API municipal/identidade, preimagens,
replay V3 integral, números, máscara e atributos de tachado, matrizes e HEAD por
OID com reservas qualificadas. --apply substitui apenas preimagens não publicadas,
com backups, trocas individuais atômicas e rollback conservador em falha.
Não realiza HTTP, staging, escrita Git, sanitização ou decisão de vigência.
"""
import argparse, collections, datetime as dt, fcntl, gzip, hashlib, json, os, re, stat, subprocess, sys
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts/bin/qa-20261027/python'),str(ROOT/'scripts')]
from auditar import validar
from auditar_municipal import metadados
from auditar_colisoes_lote_municipal import keys
from auditar_emissores_sapl import analisar
from perfil_ta_tachados_preservados_20261027 import comparar, converter, css_analisar
from auditar_commonmark_ta_v2 import NOTE
from conferir_tabelas_nativas_ta import Tabelas
from markdown_it import MarkdownIt
from preparar_reparos_escapes_ta_46_20261027 import escapar
from comum import normalizar_chave
BASE=ROOT/'municipais/_indice/_recuperacao_20261027'
RESERVAS=[('agregado921-validado-final/entrega-final.json','ca0edb15cf2054c845ad5413dc6677a377aa9ba76260b1f7afa5187d9e642ae0'),('agregado586-validado-final/entrega-final.json','a31301fc0545cb75c631b1b2fa6420aef41bb321e8fc55be83ff5254e59d7d82')]
def sha(b):return hashlib.sha256(b).hexdigest()
def info(p):
 p=p.resolve();b=p.read_bytes();return dict(arquivo=str(p.relative_to(ROOT)),sha256=sha(b),bytes=len(b))
def safe(value):
 p=Path(value)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Caminho absoluto ou traversal')
 q=ROOT/p
 if not q.resolve().is_relative_to(ROOT) or q.is_symlink():raise ValueError('Caminho externo ou symlink')
 return q

def verificar_manifesto(path,expected):
 raw=path.read_bytes()
 if sha(raw)!=expected:raise ValueError('SHA do manifesto mudou')
 m=json.loads(raw);seen=set()
 for r in m['arquivos']:
  p=r.get('arquivo',r.get('path'))
  if p in seen:raise ValueError('Artefato duplicado')
  seen.add(p);data=safe(p).read_bytes()
  if sha(data)!=r['sha256'] or len(data)!=r['bytes']:raise ValueError('Artefato diverge: '+p)
 return m

def corpo(text):return text.split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1]
def material(row):
 if row['modo']=='tachados':return row['materializacao_original']['registro']
 if sha(safe(row['materializacao']).read_bytes())!=row['sha256_materializacao']:raise ValueError('Materialização mudou')
 hits=[r for r in map(json.loads,safe(row['materializacao']).read_text().splitlines()) if r.get('path')==row['path']]
 if len(hits)!=1:raise ValueError('Materialização ambígua')
 return hits[0]

def prova_arquivo(p):
 raw=safe(p['arquivo']).read_bytes()
 if sha(raw)!=p['sha256']:raise ValueError('Fonte primária mudou')
 if p.get('metadata'):
  meta_raw=safe(p['metadata']).read_bytes()
  if sha(meta_raw)!=p['sha256_metadata']:raise ValueError('Metadado primário mudou')
  meta=json.loads(meta_raw)
 else:meta=json.loads(safe(p['arquivo']).with_suffix('.meta.json').read_text())
 if meta.get('status')!=200 or meta.get('sha256')!=sha(raw):raise ValueError('Captura sem HTTP 200/SHA')
 for k in ['url','url_final','capturado_em']:
  if k in p and meta.get(k)!=p[k]:raise ValueError('Captura diverge: '+k)
 return raw,meta

def validar_linha(row,names,require_current=True):
 old=safe(row['preimagem']).read_bytes();new=safe(row['candidato']).read_bytes();target=safe(row['path'])
 if sha(old)!=row['sha256_preimagem'] or sha(new)!=row['sha256_candidato']:raise ValueError('Preimagem/candidato congelados mudaram')
 if require_current and (not target.is_file() or target.read_bytes()!=old):raise ValueError('Preimagem corrente diverge: '+row['path'])
 om=metadados(old.decode());nm=metadados(new.decode());ob=corpo(old.decode());nb=corpo(new.decode())
 if not ob.endswith('\n') or not nb.endswith('\n') or sha(ob[:-1].encode())!=om['sha256_texto'] or sha(nb[:-1].encode())!=nm['sha256_texto']:raise ValueError('sha256_texto não confere')
 if {k:v for k,v in om.items() if k!='sha256_texto'}!={k:v for k,v in nm.items() if k!='sha256_texto'} or keys(old.decode(),row['path'])!=keys(new.decode(),row['path']):raise ValueError('Metadados/identidade alterados')
 prefix,n=re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: '+json.dumps(nm['sha256_texto']),old.decode()[:-len(ob)])
 if n!=1 or prefix!=new.decode()[:-len(nb)]:raise ValueError('Cabeçalho/H1 alterado')
 mr=material(row)
 if not mr['aprovado'] or mr['sha256']!=sha(old) or mr['gates']['anexos_proprios']!=0:raise ValueError('Gates originais não conferem')
 proofs={k:prova_arquivo(mr[k]) for k in ['prova_frontend','prova_norma','prova_ta','prova_casa']}
 source,meta=proofs['prova_frontend'];norm=json.loads(proofs['prova_norma'][0]);ta_json=json.loads(proofs['prova_ta'][0]);casa_json=json.loads(proofs['prova_casa'][0])
 if norm.get('esfera_federacao')!='M' or str(norm['id'])!=str(mr['norma_id']):raise ValueError('API esfera/ID incoerente')
 if str(norm['numero'])!=str(nm['numero']) or str(norm['ano'])!=nm['data'][:4] or norm['data']!=nm['data']:raise ValueError('Número/ano/data API incoerentes')
 tas=ta_json.get('results',[]) if isinstance(ta_json,dict) else ta_json
 ta=next((r for r in tas if r.get('id')==mr['ta_id']),None)
 if ta is None or ta.get('privacidade') not in (0,69) or ta.get('publicado') is False:raise ValueError('TA público original não encontrado')
 if str(ta.get('object_id'))!=str(norm['id']) or ta.get('data')!=norm['data'] or str(ta.get('numero'))!=str(norm['numero']) or str(ta.get('ano'))!=str(norm['ano']):raise ValueError('TA e norma divergem')
 houses=casa_json.get('results',[]) if isinstance(casa_json,dict) else casa_json
 if len(houses)!=1:raise ValueError('Casa oficial ambígua')
 house=houses[0];cities=[r for r in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text()) if str(r['id'])==str(nm['codigo_ibge'])]
 if len(cities)!=1 or normalizar_chave(cities[0]['nome'])!=normalizar_chave(house['municipio']) or normalizar_chave(nm['municipio'])!=normalizar_chave(house['municipio']) or nm['uf']!=house['uf'] or cities[0]['regiao-imediata']['regiao-intermediaria']['UF']['sigla']!=house['uf']:raise ValueError('IBGE/casa/município divergem')
 literal=mr['gates']['identidade_literal']
 if not literal.get('numero_literal_confirmado') or not literal.get('data_literal_confirmada') or literal.get('divergencias'):raise ValueError('Identidade literal original pendente')
 if nm['sha256_fonte']!=sha(source) or nm['capturado_em_fonte']!=meta['capturado_em'] or nm['baixado_em']!=dt.datetime.fromisoformat(meta['capturado_em']).astimezone(ZoneInfo('America/Recife')).date().isoformat():raise ValueError('Captura original/metadados divergem')
 if row['modo']=='escapes':
  if nb!=escapar(ob[:-1])+'\n' or nb==ob:raise ValueError('Mudança além dos escapes')
  context=safe(row['controle_contexto']);raw=context.read_bytes()
  if sha(raw)!=row['sha256_controle_contexto'] or row['path'] not in (context.parent/'aprovados.paths.txt').read_text().splitlines():raise ValueError('Contexto original não aprovado')
 elif row['modo']=='tachados':
  expected,_=converter(source.decode())
  if nb[:-1]!=expected or ob.count(NOTE)!=1 or nb.replace('~~Sebastião Alves~~\n\n~~Secretário~~\n\n','',1).rstrip('\n')!=ob.replace('\n\n'+NOTE,'').rstrip('\n'):raise ValueError('Reparo Buritis não é a mudança exata')
  if 'Secretário Substituto' not in nb or 'Nota editorial' in nb:raise ValueError('Fecho Buritis incorreto')
 else:raise ValueError('Modo não autorizado')
 css=css_analisar(source.decode(),source,row['path'],sha(new),meta.get('url_final',''),'reparos47')
 for e in css['eventos_texto_efetivo_DOM']:
  if e['escopo'] in {'ativo','epigrafe'} and (e['fonte_especial_aplicada_css'] or e['ocultacao_css'] or e.get('mso_hide_nao_padronizado') and e['mso_hide_nao_padronizado']['value'].lower()=='all'):raise ValueError('CSS aplicado requer revisão')
 selectors={r['selector'] for r in css['regras_CSS_examinadas'] if any(r.get('matches_por_estado',{}).get(k,0) for k in ['ativo','epigrafe'])}
 if css['seletores_nao_resolvidos'] or any(r['selector'] in selectors for r in css['regras_condicionais_com_match']+css['pseudo_elementos_com_match']):raise ValueError('CSS não resolvido requer revisão')
 if any(not e['rotulo_literal_revogado'] for e in css['dispositivos_ativos_classe_revogado']):raise ValueError('Classe revogado sem rótulo literal requer contexto próprio')
 replay=comparar(source.decode(),nb)
 if not replay['aprovado']:raise ValueError('Replay V3 diverge: '+str(replay.get('contexto')))
 st=Tabelas(True);st.feed(source.decode());st.close();rt=Tabelas();rt.feed(MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough').render(nb));rt.close()
 if st.current is not None or rt.current is not None or st.tables!=rt.tables:raise ValueError('Matrizes tabelas divergem')
 if analisar(nb,nm['municipio'],names):raise ValueError('Emissor/jurisdição pendentes')
 errors,warnings=validar(new.decode(),row['path'],dt.date.today())
 if errors or warnings:raise ValueError('Formato inválido: '+str((errors,warnings)))
 return old,new,dict(replay=replay,CSS=css,tabelas=len(st.tables),matrizes=st.tables,identidade_API_M_e_literal_preservada=True,metadados_exceto_sha256_texto_iguais=True,captura_original=meta['capturado_em'],gates_originais=mr['gates'])

def exportar(rows,output):
 output.mkdir(parents=True,exist_ok=False);result=[]
 for i,r in enumerate(rows):
  data=safe(r['candidato']).read_bytes()
  if sha(data)!=r['sha256_candidato']:raise ValueError('Candidato mudou antes da exportação')
  p=output/(str(i)+'.txt')
  with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  result.append(dict(path=r['path'],sha256_preimagem=r['sha256_preimagem'],sha256_candidato=r['sha256_candidato'],preparado=str(p.relative_to(ROOT))))
 return result

def fsync_dir(p):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)

def aplicar_transacao(rows,output,resolve=safe,replace=os.replace):
 """Pré-valida todos, faz backups exclusivos e troca; falha reverte só bytes próprios."""
 output.mkdir(parents=True,exist_ok=False);held=[];done=[];report=dict(aplicados=[],revertidos=[],erros_rollback=[])
 try:
  for i,r in enumerate(rows):
   target=resolve(r['path']);prep=resolve(r['preparado'])
   if target.is_symlink() or not stat.S_ISREG(target.stat().st_mode) or target.stat().st_dev!=prep.stat().st_dev:raise ValueError('Alvo inválido ou preparado em outro volume')
   f=target.open('rb');held.append((f,target,r));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);raw=f.read();inode=os.fstat(f.fileno())
   if sha(raw)!=r['sha256_preimagem'] or sha(prep.read_bytes())!=r['sha256_candidato']:raise ValueError('Preimagem/preparado divergem antes da troca')
   backup=output/(str(i)+'.txt')
   with backup.open('xb') as b:b.write(raw);b.flush();os.fsync(b.fileno())
   r=dict(r,backup=str(backup),modo=stat.S_IMODE(inode.st_mode),stat=(inode.st_dev,inode.st_ino,inode.st_size,inode.st_mtime_ns));held[-1]=(f,target,r)
  for f,target,r in held:
   st=target.lstat()
   if target.is_symlink() or (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)!=r['stat'] or sha(target.read_bytes())!=r['sha256_preimagem']:raise ValueError('Preimagem mudou durante a preparação')
  for f,target,r in held:
   st=target.lstat()
   if target.is_symlink() or (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)!=r['stat'] or sha(target.read_bytes())!=r['sha256_preimagem']:raise ValueError('Preimagem mudou imediatamente antes da troca')
   prep=resolve(r['preparado']);prep.chmod(r['modo']);replace(prep,target);done.append((target,r));fsync_dir(target.parent)
   if sha(target.read_bytes())!=r['sha256_candidato']:raise ValueError('Gravação candidata diverge')
   report['aplicados'].append(r['path'])
 except Exception as error:
  report['erro']=repr(error)
  for target,r in reversed(done):
   try:
    if target.is_symlink() or sha(target.read_bytes())!=r['sha256_candidato']:raise ValueError('Alvo mudou depois da troca; rollback recusado')
    temp=output/('rollback-'+str(len(report['revertidos']))+'.txt')
    with temp.open('xb') as f:f.write(Path(r['backup']).read_bytes());f.flush();os.fsync(f.fileno())
    temp.chmod(r['modo']);os.replace(temp,target);fsync_dir(target.parent);report['revertidos'].append(r['path'])
   except Exception as rollback:report['erros_rollback'].append(dict(path=r['path'],erro=repr(rollback)))
  (output/'transacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');raise
 finally:
  for f,_,_ in held:f.close()
 (output/'transacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report

def dedup(rows,baseline):
 m=json.loads(baseline.read_text())
 for r in m['arquivos']:
  data=safe(r['arquivo']).read_bytes()
  if sha(data)!=r['sha256'] or len(data)!=r['bytes']:raise ValueError('Baseline mudou')
 index=collections.defaultdict(set);paths=set()
 for r in map(json.loads,gzip.open(safe(m['metadados']),'rt')):
  paths.add(r['path'])
  for k in r['chaves']:index[tuple(k)].add(r['path'])
 if len(paths)!=m['total']:raise ValueError('Total baseline incoerente')
 clashes=[]
 for r in rows:
  if r['path'] in paths:raise ValueError('Destino já publicado/reservado')
  for k in keys(safe(r['candidato']).read_text(),r['path']):
   if index[k]:clashes.append(dict(path=r['path'],chave=k,existentes=sorted(index[k])))
   index[k].add(r['path'])
 if clashes:raise ValueError('Colisões: '+json.dumps(clashes,ensure_ascii=False))
 return dict(commit=m['commit'],head=m['normas_head'],comparados=m['total'],reservas=m['reservas'],candidatos=len(rows),colisoes=[])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifesto',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--saida',type=Path,required=True);p.add_argument('--apply',action='store_true',help='Exclusivo ROOT; não executar por agentes de preparação');a=p.parse_args()
 out=a.saida.resolve()
 if not out.is_relative_to(BASE.resolve()):raise ValueError('Saída precisa estar no diretório privado persistente')
 out.mkdir(parents=True,exist_ok=False);m=verificar_manifesto(a.manifesto,a.sha256);rows=json.loads(safe(m['mapa_candidatos']).read_text())['candidatos']
 if len(rows)!=47 or len({r['path'] for r in rows})!=47 or collections.Counter(r['modo'] for r in rows)!={'escapes':46,'tachados':1}:raise ValueError('Seleção diferente dos 47 fechados')
 if subprocess.check_output(['git','ls-files','-z','--',*[r['path'] for r in rows]],cwd=ROOT):raise ValueError('Destino já no índice; ROOT deve reconciliar')
 lock=(BASE/'promocao-ta47.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 names=[r['nome'] for r in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text())];proofs=[]
 for r in rows:
  _,_,proof=validar_linha(r,names);proofs.append(dict(path=r['path'],**proof))
 cmd=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for path,digest in RESERVAS:cmd+=['--reserva',str(BASE/path),digest]
 subprocess.run(cmd,cwd=ROOT,check=True);baseline=out/'baseline-head/manifesto.json';joint=dedup(rows,baseline)
 prepared=exportar(rows,out/'preparados');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if head!=joint['commit']:raise ValueError('HEAD mudou durante os gates; repetir com saída nova')
 result=dict(modo='apply' if a.apply else 'dry-run',propostas=47,promovidas=0,manifesto=info(a.manifesto),codigo=info(Path(__file__).resolve()),dedup=joint,resultados=proofs,promocao=prepared,gerado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat())
 report=out/'resultado.json';report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if a.apply:
  if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=head:raise ValueError('HEAD mudou antes da aplicação')
  result['transacao']=aplicar_transacao(prepared,out/'backups');result['promovidas']=47;report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 lock.close();print(json.dumps(dict(modo=result['modo'],propostas=47,promovidas=result['promovidas'],resultado=str(report.relative_to(ROOT)))))
if __name__=='__main__':main()
