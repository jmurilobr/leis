"""Controle pós-aplicação ROOT; nenhuma edição canônica, global ou Git."""
from pathlib import Path
import json,hashlib,subprocess,shutil
D=Path(__file__).resolve().parent;R=D.parents[2];E=R/'federal/_fonte/auditorias/export730_legado87_20261028_002';A=E/'aplicacao_ROOT_20261028T184752482511Z';B=R/'federal/_fonte/auditorias/alimentacao_normas_20261028_019';sha=lambda b:hashlib.sha256(b).hexdigest();mapping=json.loads((E/'mapa_efetivo730.json').read_bytes())
def add(p,expected=None):
 p=Path(p);p=p if p.is_absolute()else R/p;key=str(p.relative_to(R));actual=sha(p.read_bytes())
 if expected:assert actual==expected,(key,expected,actual)
 if key in mapping:assert mapping[key]==actual,key
 mapping[key]=actual
for path,digest in list(mapping.items()):add(path,digest)
for n in ['mapa_efetivo730.json','entrega-paths.txt','entrega-hashes.json']:add(E/n)
m=json.loads((B/'pacote_final001/lote_final.json').read_bytes());by={r['path']:r for r in m['publicaveis_privados']};intent=json.loads((A/'intencao.json').read_bytes());journal=[json.loads(l)for l in(A/'aplicacao.jsonl').read_bytes().splitlines()];assert len(by)==len(intent['inclusoes'])==len(journal)==730;assert set(by)=={r['path']for r in journal}=={r['path']for r in intent['inclusoes']}
for row in journal:assert row['estado']=='criado atomicamente sem sobrescrever';assert row['sha256']==by[row['path']]['sha256_candidato'];add(row['path'],row['sha256'])
for row in intent['inclusoes']:assert row['preimagem']=='ausente';assert row['sha256_final']==by[row['path']]['sha256_candidato'];add(row['backup'],row['sha256_final'])
for p in A.rglob('*'):
 if p.is_file():add(p)
P=D/'provas-ROOT';P.mkdir(exist_ok=False);sources=[]
for name in ['export730-testes-root.log','limites-export730-ROOT.json','export730-mapa-root.log','export730-dry-root-v2.log','export730-apply-root.log']:
 origin=R/'_fonte/operacao_root_20261027'/name;dest=P/(name[:-4]+'.txt'if name.endswith('.log')else name);raw=origin.read_bytes();dest.write_bytes(raw);assert sha(dest.read_bytes())==sha(raw);sources.append({'origem_ROOT':str(origin.relative_to(R)),'copia_publica':str(dest.relative_to(R)),'sha256':sha(raw),'bytes':len(raw)})
(D/'proveniencia-provas-ROOT.json').write_text(json.dumps({'provas':sources,'limites':'Cópias byte a byte das provas ROOT; originais compartilhados não alterados nem incluídos no mapa.'},ensure_ascii=False,indent=2)+'\n');whitespace=json.loads((D/'whitespace-codigo.json').read_bytes());assert whitespace['arquivos_examinados']==146 and whitespace['arquivos_com_ocorrencias']==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();(D/'controle730.json').write_text(json.dumps({'HEAD_aplicacao_ROOT':intent['HEAD'],'HEAD_no_controle':head,'aplicacao':str(A.relative_to(R)),'canônicos_ROOT':730,'backups_ROOT':730,'provas_ROOT_copiadas':len(sources),'codigo_whitespace_examinado':146,'ocorrencias_whitespace':0,'globais_incluidos':0,'WORKLOG_global_incluido':False,'registro_incluido':False,'limites':'Mapa efetivo pós-aplicação, candidatos e canônicos conferidos por SHA. Código compartilhado divergente preservado, sem staging/Git ou edição canônica pelo agente.'},ensure_ascii=False,indent=2)+'\n')
for p in D.rglob('*'):
 if p.is_file()and p.name not in {'mapa_efetivo730-posapply.json','entrega-paths.txt','entrega-hashes.json','publicar-paths.txt'}:add(p)
assert 'WORKLOG.md'not in mapping and'scripts/html2md.py'not in mapping and'scripts/baixar_federal.py'not in mapping;assert not any(p.startswith('scripts/dados/pendencias')for p in mapping);mp=D/'mapa_efetivo730-posapply.json';assert not mp.exists();mp.write_text(json.dumps(dict(sorted(mapping.items())),ensure_ascii=False,indent=2)+'\n');lp=D/'publicar-paths.txt';lp.write_text(''.join(p+'\n'for p in sorted(mapping)));files=[mp,lp]+[R/p for p in mapping];ep=D/'entrega-paths.txt';ep.write_text(''.join(str(p.relative_to(R))+'\n'for p in files));(D/'entrega-hashes.json').write_text(json.dumps({'sha256_lista':sha(ep.read_bytes()),'sha256_mapa':sha(mp.read_bytes()),'arquivos':[{'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())}for p in files]},ensure_ascii=False,indent=2)+'\n');print(len(mapping),'arquivos no mapa; SHA',sha(mp.read_bytes()),flush=True)
