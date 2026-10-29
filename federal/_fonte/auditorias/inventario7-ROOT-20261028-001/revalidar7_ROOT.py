"""Revalidação somente leitura das sete decisões individuais de integralidade."""
from pathlib import Path
import sys,json,gzip,hashlib,subprocess
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();sys.path.insert(0,str(R/'scripts'));from pendencias_integralidade import carregar
for p,d in json.loads((B/'artefatos-origem-hashes.json').read_bytes()).items():assert sha((R/p).read_bytes())==d,p
before=json.loads(gzip.decompress((B/'registro-preimagem.json.gz').read_bytes()));expected=json.loads(gzip.decompress((B/'registro-proposto.json.gz').read_bytes()));current=json.loads((R/'scripts/dados/pendencias-integralidade-publicadas.json').read_bytes());assert expected['pendentes'][:7630]==before['pendentes'];assert len(expected['pendentes'])==7637;registry=carregar(R);assert len(registry)>=7637;rows=json.loads((B/'decisoes7.json').read_bytes())['decisoes'];assert len(rows)==7
for row in rows:
 e=row['entrada_proposta'];p=e['path'];assert registry[p]['sha256_md']==e['sha256_md'];raw=subprocess.check_output(['git','-C',str(R),'show','HEAD:'+p]);assert sha(raw)==e['sha256_md'];assert gzip.decompress((R/row['preimagem']).read_bytes())==raw;src=gzip.decompress((R/row['HTML_integral']).read_bytes());assert sha(src)==e['evidencia']['sha256_HTML'];assert registry[p]['evidencia']['sha256_parecer']==sha((B/'decisoes7.json').read_bytes());assert registry[p]['evidencia']['parecer']==e['evidencia']['parecer']
assert {e['path'] for e in expected['pendentes'][7630:]}=={r['entrada_proposta']['path'] for r in rows};print('7 decisões/fontes/preimagens e blobs HEAD conferidos;7630 anteriores preservadas; registro válido, nenhum canônico alterado; sem escrita ou rede.')
