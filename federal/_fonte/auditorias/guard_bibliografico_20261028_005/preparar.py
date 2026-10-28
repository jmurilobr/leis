from pathlib import Path
import json,gzip,hashlib,base64,sys,difflib
R=Path.cwd();B=Path(__file__).resolve().parent;A=B.with_name('guard_bibliografico_20261027_004');sha=lambda b:hashlib.sha256(b).hexdigest();old=(A/'integridade_anexos_decreto.py').read_bytes();assert sha(old)=='3f581fc23aa987e6b614a9e7bd61e10f69583d07de018685b625cd59758bf466';s=old.decode();s=s.replace('(?:clbr|colecao das leis)','(?:clbr|clr|colecao das leis)').replace("r'\\(\\s*ilegivel", "r'\\(\\s*\\\\?\\s*ilegivel");(B/'integridade_anexos_decreto.py').write_text(s);(B/'guard80_antecedente.py').write_bytes(old)
for n in ['test_base74.py','test_delta.py','fixture1908.json','guard74_antecedente.py']:(B/n).write_bytes((A/n).read_bytes())
(B/'guard80_para87.patch').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),s.splitlines(True),fromfile='guard80_antecedente.py',tofile='integridade_anexos_decreto.py')))
sys.path.insert(0,str(R/'scripts'));import baixar_federal as f
from integridade_html_federal import Visivel
source=R/'federal/_fonte/auditorias/alimentacao_normas_20261028_015/retencoes_contextuais001/fontes_provas.jsonl.gz';fixtures={}
for line in gzip.decompress(source.read_bytes()).splitlines():
 x=json.loads(line);path=x['registro']['path'];num=Path(path).name.split('-')[1]
 if num not in ['14056','14722']:continue
 h=base64.b64decode(x['HTML_primario_base64']);assert sha(h)==x['registro']['sha256_HTML'];p=Visivel();p.feed(h.decode());body=f.convert(h.decode());fixtures[num]={'registro':x['registro'],'corpo':body,'sha256_corpo':sha(body.encode()),'HTML_primario_base64':x['HTML_primario_base64'],'metadados_raw':x['metadados_raw'],'visual':p.visual,'structure':p.structure}
assert set(fixtures)=={'14056','14722'};(B/'fixtures015.json.gz').write_bytes(gzip.compress(json.dumps(fixtures,ensure_ascii=False).encode(),mtime=0));(B/'recibo_preparo.json').write_text(json.dumps({'base80':{'path':str((A/'integridade_anexos_decreto.py').relative_to(R)),'sha256':sha(old)},'candidato':{'path':str((B/'integridade_anexos_decreto.py').relative_to(R)),'sha256':sha(s.encode())},'fonte_fixture98':{'path':str(source.relative_to(R)),'sha256':sha(source.read_bytes())},'limites':'Proposta privada, sem arquivo global, MD, máscara ou Git alterado. Reconhece variante bibliográfica CLR e marcador ilegível com escape Markdown remanescente; não corrige texto e não inventa representação de objeto.'},ensure_ascii=False,indent=2)+'\n');print('Proposta privada preparada, base80 preservada.')
