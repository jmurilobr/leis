"""Reconciliação somente leitura de HEAD e reservas privadas explícitas."""
from pathlib import Path
import json,gzip,hashlib,sys
B=Path(__file__).resolve().parent;R=Path.cwd();D=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002';code=(D/'validar5769_HEAD.py').read_text();prefix=code.split("selected=m['documentos']")[0];env={'__file__':str(D/'validar5769_HEAD.py')};exec(compile(prefix,'reconciliacao_HEAD_antecedente','exec'),env);docs=env['docs'];fed=env['federal'];idx=env['idx'];head=env['head'];sha=lambda b:hashlib.sha256(b).hexdigest();reserves=[]
for row in json.loads((D/'manifesto5769.json').read_bytes())['documentos']:
 if row['path'] in docs:continue
 docs[row['path']]={'path':row['path'],'meta':row['meta'],'reserva_privada5769':True};reserves.append({'path':row['path'],'sha256_MD':row['sha256_md'],'origem':'seleção imutável 5769 entregue, sem duplicar linha já pública'})
sys.path.insert(0,str(D/'codigo'));from auditar_cache_dou import meta_corpo
from identidade_cross_snapshot import number
from gate_orgao import n
for num,count in [(16,580),(17,674),(18,572)]:
 P=R/f'federal/_fonte/auditorias/alimentacao_normas_20261028_{num:03}/pacote_final001/lote_final.json';manifest=json.loads(P.read_bytes())
 for row in manifest['publicaveis_privados']:
  if row['path'] in fed:continue
  raw=(R/row['candidato']).read_bytes();assert sha(raw)==row['sha256_candidato'];meta,_=meta_corpo(raw.decode());typ=idx['tipos_explicitamente_comparaveis'].get(n(meta['tipo']));ident=number(meta['numero']);assert typ and ident;fed[row['path']]={'path':row['path'],'tipo':typ,'numero':ident,'data':meta['data'],'URN_literal':meta.get('urn'),'fonte_literal':meta.get('fonte'),'reserva_privada':True,'sha256_MD':sha(raw)};reserves.append({'path':row['path'],'sha256_MD':sha(raw),'origem':str(P.relative_to(R))})
outbase={'HEAD':head,'documentos':list(docs.values()),'reservas_privadas':reserves,'limites':'Linhas públicas e reservas privadas distintas por path; não são nova contagem de publicação.'};outidx={**idx,'HEAD':head,'registros':[r for r in fed.values()if'tipo'in r],'reservas':[r for r in fed.values()if'tipo'not in r]};outidx['MD_canonicos_ou_reservados']=len(fed)
for name,value in [('baseline_reguladores_HEAD_reservas.json.gz',outbase),('indice_federal_HEAD_reservas.json.gz',outidx)]:
 p=B/name;assert not p.exists();p.write_bytes(gzip.compress(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
receipt={'HEAD':head,'reguladores_publicos_ou_reservados':len(docs),'federais_cobertos_ou_reservados':len(fed),'reservas_sem_chave':len(outidx['reservas']),'deltas_MD_por_corpus':dict(env['counts']),'reservas_acrescentadas':len(reserves),'codigo_reconciliador':str((D/'validar5769_HEAD.py').relative_to(R)),'sha256_codigo_reconciliador':sha((D/'validar5769_HEAD.py').read_bytes()),'arquivos':[{'path':str((B/f).relative_to(R)),'sha256_gzip':sha((B/f).read_bytes())}for f in ['baseline_reguladores_HEAD_reservas.json.gz','indice_federal_HEAD_reservas.json.gz']],'limites':'Séries federais com chave explícita; reservas sem chave preservadas. Nenhuma identidade municipal fundida com federal por número/ano. Não é dedup universal.'};(B/'recibo_baseline.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False),flush=True)
