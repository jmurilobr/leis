"""Delta apenas diagnóstico; nunca aplica máscara ou altera guard vivo."""
from pathlib import Path
import sys,json,gzip,hashlib,re
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(B));import integridade_anexos_decreto as new,guard74_antecedente as old
sys.path.insert(0,str(R/'scripts'));import baixar_federal as f
from baixar_camara import corpo_norma
from integridade_html_federal import Visivel
sha=lambda b:hashlib.sha256(b).hexdigest();loader=R/'federal/_fonte/auditorias/diagnostico_glifos1347_20261027_002/diagnosticar.py';s=loader.read_text();ns={'__file__':str(loader),'__name__':'delta_fontes'};exec(compile(s[:s.index('lexical=[]')],'loader1347','exec'),ns);docs=[{'path':d['path'],'raw':d['source_raw'],'text':corpo_norma(d['source']) if d['lote']=='145' else d['source']} for d in ns['docs']];C=R/'federal/_fonte/auditorias/alimentacao_normas_20261027_010';prep=json.loads((C/'qa_final_v4/preparo.json').read_bytes())
for r in prep['registros']:
 raw=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());assert sha(raw)==r['sha256_html'];docs.append({'path':r['path'],'raw':raw,'text':raw.decode()})
assert len(docs)==2468;changes=[]
for d in docs:
 p=Visivel();p.feed(d['text']);body=f.convert(d['text']);a=old.anexo_proprio_ausente(body,p);b=new.anexo_proprio_ausente(body,p)
 if bool(a)!=bool(b):changes.append({'path':d['path'],'sha256_HTML':sha(d['raw']),'anterior':a,'candidato':b})
result={'fontes_examinadas':len(docs),'mudancas_de_estado':len(changes),'registros':changes,'fontes':'1.347 fontes integrais dos pacotes 145/454/748 e 1.121 fontes do preparo 010. Não reapresenta as 24 retidas como publicáveis.','limites':'Delta diagnóstico, não auditoria humana universal nem máscara. O caso real 1.908 está em fixture separada e já retido antes dos lotes; por isso não pertence ao grupo 1.347.'};(B/'delta2468.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['fontes_examinadas'],result['mudancas_de_estado'],'mudanças; nenhuma máscara.')
