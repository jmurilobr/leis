from pathlib import Path
import sys,json,hashlib,ast,os,datetime
R=Path.cwd().resolve();S=R/'scripts/estados/snapshots/ac_legis_promocao_20261027_006';sys.path.insert(0,str(S));import promover_legis_ac_privado as f
sha=lambda b:hashlib.sha256(b).hexdigest();code=(S/'promover_legis_ac_privado.py').read_bytes();assert sha(code)=='9c4ff8f76d3837e9dfe1ba62d9ad560155d05108ed2ccd83db70f53b1535639a'
# Reaproveita todas as validações congeladas; somente a regra de presença vira
# igualdade exata dos85 canônicos criados pelo journal interrompido.
tree=ast.parse(code);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validar');hits=[]
for i,x in enumerate(fn.body):
 if isinstance(x,ast.For):
  for j,node in enumerate(x.body):
   if isinstance(node,ast.If) and 'destino já existe em disco' in ast.unparse(node):hits.append((x,j))
assert len(hits)==1
loop,j=hits[0];loop.body[j]=ast.parse("if os.path.lexists(relpath(root,r['path'])) and digest(relpath(root,r['path']))!=r['sha256_md']:raise ValueError('preimagem criada diverge do candidato')").body[0];env=dict(vars(f));exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'validacao_recuperacao679','exec'),env)
A=R/'estaduais/AC/_fonte/auditorias/ac679-ROOT-apply-20261028';old=json.loads((A/'intencao.json').read_bytes());journal=[json.loads(x) for x in (A/'journal.jsonl').read_text().splitlines()];assert len(journal)==85;done={r['path']:r['sha256'] for r in journal};assert len(done)==85
m,candidates=env['validar'](R,R/old['manifesto'],R/old['mapa_sha'],679);assert sha((R/old['manifesto']).read_bytes())==old['sha256_manifesto'] and sha((R/old['mapa_sha']).read_bytes())==old['sha256_mapa'];assert [r['path'] for r in candidates[:85]]==[r['path'] for r in journal]
for r,orig in zip(candidates,old['documentos']):
 assert r['path']==orig['path'] and r['sha256_md']==orig['sha256'];assert f.digest(R/orig['backup_candidato'])==r['sha256_md'];p=R/r['path']
 if p.exists():assert r['path'] in done and f.digest(p)==done[r['path']]==r['sha256_md']
 else:assert r['path'] not in done
C=R/('estaduais/AC/_fonte/auditorias/ac679-ROOT-recuperacao-20261028-'+('apply' if '--apply' in sys.argv else 'dryrun'));C.mkdir(exist_ok=False);head,rows=f.ler_HEAD(R,C);f.conferir_dedup(rows,candidates);assert f.run_git(R,'rev-parse','HEAD').decode().strip()==head
proof={'HEAD':head,'controle_original':str(A.relative_to(R)),'journal_original_sha256':f.digest(A/'journal.jsonl'),'criados_antes':85,'restantes':594,'total':679,'codigo_original_sha256':sha(code),'sha256_runner_recuperacao':f.digest(Path(__file__)),'documentos':old['documentos'],'limite':'Todas as validações006 originais reaproveitadas; presença aceita somente se SHA bate com candidato, backup e journal85. Dedup integral contra novo HEAD. Nenhum canônico preexistente é reescrito.'};f.gravar_json(C/'intencao.json',proof)
if '--apply' not in sys.argv:print('ROOT recuperação679 dryrun:85 existentes iguais por SHA,594 ausentes, dedup e validação integral aprovados');raise SystemExit(0)
with (C/'journal.jsonl').open('x') as log:
 for r,orig in zip(candidates[85:],old['documentos'][85:]):
  assert f.run_git(R,'rev-parse','HEAD').decode().strip()==head;target=R/r['path'];assert not os.path.lexists(target);target.parent.mkdir(parents=True,exist_ok=True);raw=(R/orig['backup_candidato']).read_bytes();assert sha(raw)==r['sha256_md'];f.publicar_sem_substituir(target,raw);assert f.digest(target)==r['sha256_md'];log.write(json.dumps({'path':r['path'],'sha256':r['sha256_md'],'criado_em':f.agora()})+'\n');log.flush();os.fsync(log.fileno())
assert all(f.digest(R/r['path'])==r['sha256_md'] for r in candidates);assert f.run_git(R,'rev-parse','HEAD').decode().strip()==head;f.gravar_json(C/'resultado.json',{'total':679,'criados_antes':85,'criados_agora':594,'HEAD':head,'sem_sobrescritas':True});print('ROOT recuperação679:594 criados exclusivamente,679 totais conferidos por SHA; zero sobrescritas')
