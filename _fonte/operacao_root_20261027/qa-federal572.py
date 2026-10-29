from pathlib import Path
import ast,runpy,sys
R=Path.cwd().resolve();target=Path(sys.argv[1]).resolve();assert R/'federal/_fonte/auditorias' in target.parents and target.suffix=='.py';sys.path[:0]=[str(target.parent),str(R/'scripts'),str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts/bin/qa-html5-20261027/python')];sys.argv=[str(target),*sys.argv[2:]]
if target.name=='testes_limites572.py':
 out=R/'_fonte/operacao_root_20261027/testes_limites572-ROOT.json';assert not out.exists();tree=ast.parse(target.read_text());sinks=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='write_text'];assert len(sinks)==1 and ast.unparse(sinks[0].func.value)=="B / 'testes_limites572.json'";sinks[0].func.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(out))],keywords=[]);ast.fix_missing_locations(tree);exec(compile(tree,str(target),'exec'),{'__name__':'__main__','__file__':str(target),'__package__':None})
else:runpy.run_path(str(target),run_name='__main__')
