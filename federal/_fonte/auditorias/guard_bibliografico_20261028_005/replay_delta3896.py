"""Delta apenas diagnóstico; nunca aplica máscara ou altera guard vivo."""
from pathlib import Path
import sys,json,gzip,hashlib,re,base64,subprocess
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(B));import integridade_anexos_decreto as new,guard80_antecedente as old
sys.path.insert(0,str(R/'scripts'));import baixar_federal as f
from baixar_camara import corpo_norma
from integridade_html_federal import Visivel
sha=lambda b:hashlib.sha256(b).hexdigest();loader=R/'federal/_fonte/auditorias/diagnostico_glifos1347_20261027_002/diagnosticar.py';s=loader.read_text();ns={'__file__':str(loader),'__name__':'delta_fontes'};exec(compile(s[:s.index('lexical=[]')],'loader1347','exec'),ns);docs=[{'path':d['path'],'raw':d['source_raw'],'text':corpo_norma(d['source']) if d['lote']=='145' else d['source']} for d in ns['docs']];C=R/'federal/_fonte/auditorias/alimentacao_normas_20261027_010';prep=json.loads((C/'qa_final_v4/preparo.json').read_bytes())
for r in prep['registros']:
 raw=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());assert sha(raw)==r['sha256_html'];docs.append({'path':r['path'],'raw':raw,'text':raw.decode()})
assert len(docs)==2468
selected_late=set();provenance=[]
for date,number,package in [(20261027,13,1),(20261028,14,2),(20261028,15,1)]:
 C=R/f'federal/_fonte/auditorias/alimentacao_normas_{date}_{number:03}';M=C/f'pacote_final{package:03}/lote_final.json';manifest=json.loads(M.read_bytes());selected_late.update(r['path'] for r in manifest['publicaveis_privados']);provenance.append({'path':str(M.relative_to(R)),'sha256':sha(M.read_bytes())})
 rows=json.loads((C/'qa_final_v4/preparo.json').read_bytes())['registros'] if number==15 else manifest['publicaveis_privados']
 for r in rows:
  source=r['coleta']['texto'] if 'coleta' in r else r['fontes']['texto'];raw=gzip.decompress((R/source['arquivo_raw']).read_bytes());assert sha(raw)==(r['sha256_html'] if 'sha256_html' in r else r['sha256_HTML']);docs.append({'path':r['path'],'raw':raw,'text':raw.decode()})
assert len(docs)==3896 and len({d['path'] for d in docs})==3896
changes=[];proofs=[];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
for d in docs:
 p=Visivel();p.feed(d['text']);body=f.convert(d['text']);a=old.anexo_proprio_ausente(body,p);b=new.anexo_proprio_ausente(body,p)
 if bool(a)!=bool(b):
  query=subprocess.run(['git','show',head+':'+d['path']],cwd=R,capture_output=True);md=query.stdout if query.returncode==0 else None;row={'path':d['path'],'sha256_HTML':sha(d['raw']),'anterior':a,'candidato':b,'selecionado_lotes013_015':d['path'] in selected_late,'HEAD':head,'sha256_MD_HEAD':sha(md) if md is not None else None,'estado_HEAD':'presente' if md is not None else 'ausente','edicao_facs_atual':bool(md and b'fac-s' in md and b'![' in md),'limites':'Delta do predicado sobre fonte preservada; não comprova ausência no ato nem autoriza máscara automática. Eventual edição recuperada atual deve ser confrontada independentemente.'};changes.append(row);proofs.append({'registro':row,'HTML_original_base64':base64.b64encode(d['raw']).decode(),'corpo_convertido':body,'MD_HEAD_utf8':md.decode() if md is not None else None})
result={'fontes_examinadas':len(docs),'mudancas_de_estado':len(changes),'mudancas_nos_selecionados013_015':sum(r['selecionado_lotes013_015'] for r in changes),'registros':changes,'proveniencia':provenance,'limites':'Comparação privada entre guard80 e proposta87 em 2468 fontes do replay anterior, 480 selecionadas013, 439 selecionadas014 e509 candidatas015. Retidos não foram promovidos. Nenhuma máscara, canônico ou módulo vivo alterado.'};(B/'delta3896.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(B/'provas_delta.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proofs)+'\n').encode(),mtime=0));print(result['fontes_examinadas'],result['mudancas_de_estado'],'mudanças; selecionados',result['mudancas_nos_selecionados013_015']);assert result['mudancas_nos_selecionados013_015']==0
