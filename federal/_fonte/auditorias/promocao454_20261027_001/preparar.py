from pathlib import Path
import ast,json,hashlib
B=Path(__file__).resolve().parent;ROOT=B.parents[3];A=B.parent/'alimentacao_normas_20261027_008';Q=B.parent/'alimentacao_normas_20261027_009';sha=lambda b:hashlib.sha256(b).hexdigest();node=next(n for n in ast.parse((Q/'qualificar_snapshot_v4.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='principal_fechos');helper='"""Predicado conservador congelado; só delimita avaliação, nunca remove corpo."""\n'+ast.get_source_segment((Q/'qualificar_snapshot_v4.py').read_text(),node)+'\n';(B/'limites_principal.py').write_text(helper)
s=(A/'replay_portavel_final.py').read_text();s=s.replace("D=B/'pacote_final001'", "D=ROOT/'federal/_fonte/auditorias/alimentacao_normas_20261027_008/pacote_final003'").replace("(B/'qualificar_snapshot_v3.py')", "(B/'limites_principal.py')")
s=s.replace("receipt=json.loads((B/'recibo_replay_portavel_final.json').read_bytes())", "receipt=json.loads((B/'recibo454.json').read_bytes())")
s=s.replace("public={r['path']:r for r in manifest['publicaveis_privados']};", "public={r['path']:r for r in manifest['publicaveis_privados']};assert len(public)==454;held={r['path'] for r in json.loads((D/'retencoes13.json').read_bytes())};assert len(held)==13 and not set(public)&held;")
s=s.replace("text=htmlraw.decode('utf-8');converted=", "enc=f.escolher_texto(api);assert enc==r['fontes']['encoding_escolhido'];assert enc['contentUrl'].replace('/api/binario/','/api/public/binario/')==r['fontes']['texto']['url'];assert r['fontes']['texto']['sha256_raw']==sha(htmlraw) and r['fontes']['metadados']['sha256_raw']==sha(api_raw);assert (ROOT/r['candidato']).read_bytes()==md; text=htmlraw.decode('utf-8');converted=")
(B/'replay454.py').write_text(s)
receipt0=json.loads((A/'recibo_replay_portavel_final.json').read_text());codes=[]
for r in receipt0['codigos']:
 p=ROOT/r['path']
 if p.name=='qualificar_snapshot_v3.py':continue
 codes.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())})
codes.extend({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in [B/'limites_principal.py',Path(__file__)])
receipt={'escopo':'454 candidatos integrais; sucessor conservador exclui 13 atribuições inconclusivas de fecho. Replay portátil reconstrói limites principal/incorporados antes de comparar o fecho, usando predicado congelado separado; não é substituição de contagem no replay antigo.','sha256_runner':sha((B/'replay454.py').read_bytes()),'sha256_manifesto':sha((A/'pacote_final003/lote_final.json').read_bytes()),'codigos':codes,'limites':'Só delimita avaliação do principal. Corpo, documentos incorporados e fontes integrais sempre preservados e comparados. Sem rede ou promoção; não certifica CSS ou vigência.'};(B/'recibo454.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
