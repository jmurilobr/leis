"""Somente leitura: diff --no-index por arquivo, sem alterar snapshots."""
from pathlib import Path
import subprocess,json,hashlib,collections
D=Path(__file__).resolve().parent;R=D.parents[2];sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for name in ['export730_legado87_20261028_001','export730_legado87_20261028_002']:
 E=R/'federal/_fonte/auditorias'/name
 for p in sorted(E.rglob('*')):
  if not p.is_file()or'__pycache__'in p.parts or'aplicacao_ROOT_'in str(p)or p.suffix not in {'.py','.js','.mjs'}:continue
  result=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(p)],cwd=R,capture_output=True,text=True);assert result.returncode in {0,1,2},(p,result.returncode);text=result.stdout+result.stderr;origin='upstream de biblioteca preservado por SHA'if'/vendor/'in str(p)else'código de projeto exportado sob SHA original'if'/codigo/'in str(p)else'código próprio do complemento';rows.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'proveniencia':origin,'codigo_saida':result.returncode,'ocorrencias_diff_check':text.splitlines()})
out={'comando':'git diff --no-index --check /dev/null <arquivo>','arquivos_examinados':len(rows),'arquivos_com_ocorrencias':sum(bool(r['ocorrencias_diff_check'])for r in rows),'por_proveniencia':dict(collections.Counter(r['proveniencia']for r in rows if r['ocorrencias_diff_check'])),'registros':rows,'limites':'Nenhum snapshot ou arquivo upstream foi corrigido. Ocorrências devem ser avaliadas por proveniência antes de qualquer ratificação; não há dispensa geral para código próprio.'};(D/'whitespace-codigo.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['arquivos_examinados'],out['arquivos_com_ocorrencias'],out['por_proveniencia']);print([(r['path'],r['ocorrencias_diff_check'][:3])for r in rows if r['ocorrencias_diff_check']])
