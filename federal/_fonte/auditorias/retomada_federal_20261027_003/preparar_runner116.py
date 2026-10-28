from pathlib import Path
import json,hashlib,ast,subprocess
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];PACK=BASE.parent/'retomada_federal_20261027_002';sha=lambda b:hashlib.sha256(b).hexdigest();records=[];proof=[]
for name in ['resultado020.json','resultado021_final.json']:
 p=PACK/name;j=json.loads(p.read_text());assert j['resumo']['divergencias']==0 and j['resumo']['aprovados']==j['resumo']['auditados'];records+=j['registros'];proof.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())})
assert len(records)==3608 and len({r['path'] for r in records})==3608
p=BASE/'replay3608_cumulativo.json';assert not p.exists();p.write_text(json.dumps({'escopo':'Composição imutável dos dois replays integrais já concluídos, sem repetir auditoria nem alterar resultados antigos.','resumo':{'auditados':3608,'aprovados':3608,'divergencias':0},'provas':proof,'registros':records},ensure_ascii=False,indent=2)+'\n')
s=(BASE.parent/'retomada_federal_20261027_001/promover395.py').read_text();s=s.replace("BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sha=", "BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];PACK=BASE.parent/'retomada_federal_20261027_002';sha=")
s=s.replace('recibo_promocao395.json','recibo_promocao116.json').replace("BASE/'verificacao_9061.json'","PACK/'verificacao_3608.json'").replace("BASE/'promocoes_395.json'","PACK/'promocoes_116.json'").replace("BASE/'fontes9061/mapa_fontes9061.json'","PACK/'fontes3608/mapa_fontes3608.json'").replace("BASE/'publicar9061-completo-hashes-v2.json'","PACK/'publicar3608-hashes.json'").replace("BASE/'replay_9061_resultado.json'","BASE/'replay3608_cumulativo.json'").replace("BASE/'github_sete/resultado.json'","BASE/'github_dois/resultado.json'")
s=s.replace('9061','3608').replace('9.061','3.608').replace('395','116').replace("{'chamadas':7,'aprovados':7,'divergencias':0}","{'chamadas':2,'aprovados':2,'divergencias':0}")
anchor="print('Validação integral concluída:"
pos=s.index(anchor)
extra='''# Additional current-HEAD check by number/year, scoped to the selected years.
years=sorted({v['data'][:4] for v in vs.values()})
tree=subprocess.check_output(['git','ls-tree','-rz','HEAD','--']+['federal/decretos/'+y for y in years],cwd=ROOT)
def number_key(value):return re.sub(r'[.\\s]','',value).upper().lstrip('0') or '0'
selected={(number_key(v['numero']),v['data'][:4]) for v in vs.values()}
for entry in tree.split(b'\\0'):
 if not entry:continue
 path=entry.split(b'\\t',1)[1].decode();match=re.fullmatch(r'federal/decretos/(\\d{4})/dec-(.+)-\\d{4}-\\d\\d-\\d\\d.md',path)
 if match:assert (number_key(match[2]),match[1]) not in selected,('Colisão número/ano em HEAD',path)
'''
s=s[:pos]+extra+s[pos:];p=BASE/'promover116.py';assert not p.exists();p.write_text(s);ast.parse(s)
files=[PACK/n for n in ['verificacao_3608.json','promocoes_116.json','publicar3608-hashes.json','fontes3608/mapa_fontes3608.json','validacao_arquivo_publico3608.json','inventario3608.json']]+[BASE/'replay3608_cumulativo.json',BASE/'github_dois/resultado.json'];inputs=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in files]
r={'escopo':'Runner116 preparado para revisão ROOT; apenas AST conferida, nunca executado pelo agente. Default valida sem escrever; --apply somente ROOT, após validação integral de todos os insumos e ausência em HEAD por path/número/ano.','sha256_runner':sha((BASE/'promover116.py').read_bytes()),'HEAD_preparacao':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'insumos':inputs,'limites':'Nenhum Git de escrita, rede ou conversor é executado pelo runner. Dois renders oficiais novos entram como complemento; CSS não certificado. Pacotes 9061/3608 e registro permanecem intactos.'};(BASE/'recibo_promocao116.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');ps=[BASE/'promover116.py',BASE/'recibo_promocao116.json',BASE/'replay3608_cumulativo.json',Path(__file__)]+list((BASE/'github_dois').iterdir())+[BASE/'render_github_dois.py'];paths=sorted(set(str(p.relative_to(ROOT)) for p in ps));lp=BASE/'runner116-complemento-paths.txt';lp.write_text('\n'.join(paths)+'\n');(BASE/'runner116-complemento-hashes.json').write_text(json.dumps({'sha256_lista_paths':sha(lp.read_bytes()),'arquivos':[{'path':p,'sha256':sha((ROOT/p).read_bytes()),'bytes':(ROOT/p).stat().st_size} for p in paths]},ensure_ascii=False,indent=2)+'\n');print('Runner116 somente AST, não executado; artefatos',len(paths),'SHA',sha((BASE/'promover116.py').read_bytes()))
