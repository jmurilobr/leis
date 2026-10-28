from pathlib import Path
import sys,ast,re,datetime,json
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from identidade_decreto_revisao import normal,FECHO,MESES
from estados import pe_fidelidade_visivel as v
node=next(n for n in ast.parse((ROOT/'federal/_fonte/auditorias/alimentacao_normas_20261027_013/qualificar_snapshot_v4.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='principal_fechos');ns=globals();exec(compile(ast.Module(body=[node],type_ignores=[]),'principal_v4','exec'),ns)
closing='Rio de Janeiro, 27 de janeiro de 1939, 118º da Independência e 51º da República.'
cases=[('principal com artigo e fecho','Art. 1º Fica aprovado.\n\n'+closing,1),('principal sem artigos seguido de instruções','Resolve aprovar as instruções.\n\n'+closing+'\n\nGETULIO VARGAS\n\nInstruções\n\nArt. 1º Serviço.\n\n'+closing,0),('principal sem fecho antes de regimento','Art. 1º Aprova.\n\nRegimento\n\nArt. 1º Serviço.\n\n'+closing,0),('fecho próprio antes de fecho incorporado','Art. 1º Aprova.\n\n'+closing+'\n\nGETULIO VARGAS\n\nRegimento\n\nArt. 1º Serviço.\n\nRio de Janeiro, 28 de janeiro de 1939.',1),('artigo em quebra no mesmo bloco','DECRETA:\n  \nArtigo único. Fica autorizado.\n\n'+closing,1),('instruções sem comando próprio','Instruções\n\nArt. 1º Serviço.\n\n'+closing,0),('tabela própria antes de fecho','Art. 1º Aprova.\n\nTabela\n\nRio de Janeiro, 28 de janeiro de 1939.',0),('citação dentro de artigo não é cabeçalho','Art. 1º Altera o Regulamento citado.\n\n'+closing,1)]
out=[]
for name,body,n in cases:
 found,boundary=principal_fechos(body);assert len(found)==n,(name,found,boundary);out.append({'caso':name,'fechos_esperados':n,'fechos_obtidos':len(found),'limite':boundary,'aprovado':True})
(B/'testes_limites480.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(len(out),'regressões passaram')
