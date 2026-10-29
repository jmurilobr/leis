from pathlib import Path
import json,hashlib,datetime,collections,ast
B=Path(__file__).resolve().parent;R=B.parents[3];A=B.parent/'promocao1155_20261027_001';D=B.parent/'promocao572_20261028_001';D.mkdir(exist_ok=False);sha=lambda b:hashlib.sha256(b).hexdigest()
for name in ['promover1155.py','replay1155.py','testes_limites1155.py','testes_seguranca1155.py']:
 s=(A/name).read_text().replace('alimentacao_normas_20261027_012','alimentacao_normas_20261028_018').replace('1155','572').replace('retencoes17','retencoes').replace('fontes_provas17','fontes_provas').replace('len(held)==17','len(held)==18').replace('17 retidos','18 retidos').replace('pacote_final001','pacote_final001')
 (D/name.replace('1155','572')).write_text(s);ast.parse(s)
# Use the new portable replay body and its exact receipt, not a replay of the previous package.
s=(B/'replay_portavel_final.py').read_text().replace("receipt=json.loads((B/'recibo_replay_portavel_final.json').read_bytes())","receipt=json.loads((B/'recibo572.json').read_bytes())").replace("D=B/'pacote_final001'","D=ROOT/'federal/_fonte/auditorias/alimentacao_normas_20261028_018/pacote_final001'").replace("(B/'qualificar_snapshot_v4.py')","(ROOT/'federal/_fonte/auditorias/alimentacao_normas_20261028_018/qualificar_snapshot_v4.py')")
(D/'replay572.py').write_text(s);rr=json.loads((B/'recibo_replay_portavel_final.json').read_bytes());rr['sha256_runner']=sha((D/'replay572.py').read_bytes());(D/'recibo572.json').write_text(json.dumps(rr,ensure_ascii=False,indent=2)+'\n')
lp=B/'pacote_final001/entrega-paths.txt';files=[R/p for p in lp.read_text().splitlines()]+[B/n for n in ['replay_portavel_final.py','recibo_replay_portavel_final.json','preparar_replay_portavel.py','replay_portavel_final.log']]+[D/'replay572.py',D/'recibo572.json',Path(__file__)]
rc={'escopo':'572 inclusões privadas Normas 018; 18 retenções contextuais separadas. Dry-run padrão; --apply exclusivo ROOT, nunca executado pelo agente. Corpo integral preservado, limites apenas para avaliar fecho principal.','sha256_runner':sha((D/'promover572.py').read_bytes()),'insumos':[{'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())} for p in dict.fromkeys(files)]}
(D/'recibo_promocao572.json').write_text(json.dumps(rc,ensure_ascii=False,indent=2)+'\n');print(D)
