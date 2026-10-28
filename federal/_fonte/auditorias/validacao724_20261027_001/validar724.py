"""ROOT: valida fontes e seleção 724 já criada no disco; nenhuma escrita."""
from pathlib import Path
import sys,json,hashlib,re,subprocess
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();D=R/'federal/_fonte/auditorias/alimentacao_normas_20261027_009/pacote_final002';hs=json.loads((D/'entrega-hashes.json').read_bytes());assert sha((D/'entrega-paths.txt').read_bytes())==hs['sha256_lista']
for r in hs['arquivos']:assert sha((R/r['path']).read_bytes())==r['sha256'],r['path']
subprocess.run([sys.executable,str(B/'replay724.py')],cwd=R,check=True);m=json.loads((D/'lote_final.json').read_bytes());rows=m['publicaveis_privados'];assert len(rows)==724;ids=set();paths=set();urns=set();canonical_present=0
for r in rows:
 raw=(R/r['candidato']).read_bytes();assert sha(raw)==r['sha256_candidato'];p=R/r['path'];assert r['path'] not in paths and r['urn'] not in urns;ident=(str(int(r['numero'])),r['data'][:4]);assert ident not in ids;ids.add(ident);paths.add(r['path']);urns.add(r['urn'])
 if p.exists():assert sha(p.read_bytes())==r['sha256_candidato'];canonical_present+=1
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();check=subprocess.run(['git','cat-file','--batch-check'],cwd=R,input=''.join(head+':'+p+'\n' for p in sorted(paths)),capture_output=True,text=True,check=True);assert len(check.stdout.splitlines())==724 and all(x.endswith(' missing') for x in check.stdout.splitlines());years=sorted({y for n,y in ids});tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--']+['federal/decretos/'+y for y in years],cwd=R)
for p in tree.decode().split('\0'):
 match=re.fullmatch(r'federal/decretos/(\d{4})/dec-(\d+)-\d{4}-\d\d-\d\d\.md',p)
 if match:assert (str(int(match[2])),match[1]) not in ids
excluded=json.loads((D/'retencoes24.json').read_bytes());assert len(excluded)==24 and not paths&{r['path'] for r in excluded};root_excluded_present=0
for r in excluded:
 p=R/r['path']
 if p.exists():assert sha(p.read_bytes())==r['sha256_canonico_ROOT_em_disco'];root_excluded_present+=1
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==head
print('724 fontes/candidatos validados; '+str(canonical_present)+' canônicos ROOT iguais por SHA, 24 excluídos da seleção ('+str(root_excluded_present)+' ainda no disco, não alterados). Dedup HEAD '+head+' aprovado. Nenhuma escrita, promoção, remoção ou Git de escrita.')
