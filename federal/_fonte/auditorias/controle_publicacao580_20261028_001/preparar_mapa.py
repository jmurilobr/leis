"""Mapa flat de staging ROOT; leitura dos insumos e escrita somente neste controle."""
from pathlib import Path
import json,hashlib,collections
R=Path.cwd();D=Path(__file__).resolve().parent;B=R/'federal/_fonte/auditorias/alimentacao_normas_20261028_016';P=R/'federal/_fonte/auditorias/promocao580_20261028_001';A=P/'aplicacao_ROOT_20261028T162838340240Z';sha=lambda b:hashlib.sha256(b).hexdigest();mapping={};origins=collections.defaultdict(list)
def add(path,digest=None,origin='insumo'):
 p=Path(path);p=p if p.is_absolute()else R/p;rel=str(p.relative_to(R));raw=p.read_bytes();actual=sha(raw)
 if digest:assert actual==digest,(rel,digest,actual)
 if rel in mapping:assert mapping[rel]==actual,rel
 mapping[rel]=actual
 if origin not in origins[rel]:origins[rel].append(origin)
for receipt in [B/'pacote_final001/entrega-hashes.json',B/'entrega-replay-portavel-hashes.json',P/'entrega-hashes.json']:
 o=json.loads(receipt.read_bytes());add(receipt,origin='recibo antecedente congelado')
 for row in o['arquivos']:add(row['path'],row['sha256'],'artefato de entrega congelada')
 name='entrega-paths.txt'if receipt.parent!=B else'entrega-replay-portavel-paths.txt';lp=receipt.parent/name;assert sha(lp.read_bytes())==o['sha256_lista'];add(lp,origin='lista antecedente congelada')
for name in ['recibo580.json','recibo_promocao580.json']:
 r=json.loads((P/name).read_bytes())
 for row in r.get('codigos',[])+r.get('insumos',[]):add(row['path'],row['sha256'],'dependência ou insumo por SHA do runner')
m=json.loads((B/'pacote_final001/lote_final.json').read_bytes());intent=json.loads((A/'intencao.json').read_bytes());journal=[json.loads(l)for l in(A/'aplicacao.jsonl').read_bytes().splitlines()];assert len(intent['inclusoes'])==len(journal)==len(m['publicaveis_privados'])==580;by={r['path']:r for r in m['publicaveis_privados']};assert set(by)=={r['path']for r in journal}=={r['path']for r in intent['inclusoes']}
for r in journal:assert r['estado']=='criado atomicamente sem sobrescrever';add(r['path'],r['sha256'],'canônico criado exclusivamente pelo ROOT');assert r['sha256']==by[r['path']]['sha256_candidato']
for r in intent['inclusoes']:add(r['backup'],r['sha256_final'],'backup de candidato na aplicação ROOT');assert r['sha256_final']==by[r['path']]['sha256_candidato']and r['preimagem']=='ausente'
for p in A.rglob('*'):
 if p.is_file():add(p,origin='journal, intenção, fonte ou backup da aplicação ROOT')
for p in (R/'_fonte/operacao_root_20261027').glob('federal580-*-root.log'):add(p,origin='log de conferência ROOT')
for name in ['testes_limites580-ROOT.json','qa-federal580.py']:add(R/'_fonte/operacao_root_20261027'/name,origin='prova ou receita de conferência ROOT')
add(Path(__file__),origin='receita deste mapa, sem Git');mp=D/'mapa_flat580.json';assert not mp.exists();mp.write_text(json.dumps(dict(sorted(mapping.items())),ensure_ascii=False,indent=2)+'\n');lp=D/'publicar580-paths.txt';lp.write_text(''.join(p+'\n'for p in sorted(mapping)));summary={'mapa':str(mp.relative_to(R)),'sha256_mapa':sha(mp.read_bytes()),'lista':str(lp.relative_to(R)),'sha256_lista':sha(lp.read_bytes()),'arquivos':len(mapping),'canônicos_ROOT':580,'backups_ROOT':580,'bytes':sum((R/p).stat().st_size for p in mapping),'origens_por_path':dict(origins),'limites':'Nenhum WORKLOG incluído, Git de escrita ou alteração dos insumos. Mapa reúne entregas congeladas, dependências por SHA, canônicos aplicados pelo ROOT, backups/journal/fontes e provas ROOT. Arquivos deste controle não se auto-hasheiam; manifesto separado os identifica.'};(D/'controle580.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print('Mapa flat',len(mapping),'arquivos',summary['sha256_mapa'],flush=True)
