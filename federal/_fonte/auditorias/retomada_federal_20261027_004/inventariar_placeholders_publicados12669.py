from pathlib import Path
import json,gzip,hashlib,re,sys,subprocess,collections
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));from estados.pe_fidelidade_visivel import texto_visivel_html
from integridade_html_federal import Visivel
sha=lambda b:hashlib.sha256(b).hexdigest();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();records=[];proof=[];by={}
for s,n in [('001','9061'),('002','3608')]:
 p=ROOT/f'federal/_fonte/auditorias/retomada_federal_20261027_{s}/fontes{n}/fontes{n}_parte001.jsonl.gz';count=0;hits=0
 with gzip.open(p,'rt') as f:
  for line in f:
   r=json.loads(line);assert sha(r['html_original'].encode())==r['sha256_html'] and sha(r['md_final'].encode())==r['sha256_md_final'];count+=1;v=texto_visivel_html(r['html_original']);ms=list(re.finditer(r'(?:<<|«)\s*(?:anexo|tabela|quadro)s?\s*(?:>>|»)',v,re.I))
   if not ms:continue
   hits+=1;sp=Visivel();sp.feed(r['html_original']);raw=subprocess.check_output(['git','show',head+':'+r['path']],cwd=ROOT);oid=subprocess.check_output(['git','rev-parse',head+':'+r['path']],cwd=ROOT,text=True).strip();contexts=[]
   for m in ms:
    a=max(v.rfind('Art.',0,m.start()),v.rfind('Artigo',0,m.start()),max(0,m.start()-1500));contexts.append({'literal':m.group(),'offset_visivel':m.start(),'contexto':v[a:m.end()+700]})
   rec={'pacote':n,'path':r['path'],'urn':r['urn'],'numero':r['numero'],'data':r['data'],'HEAD':head,'OID_HEAD':oid,'sha256_md_HEAD':sha(raw),'sha256_md_pacote':r['sha256_md_final'],'HEAD_igual_entrega':sha(raw)==r['sha256_md_final'],'sha256_html':r['sha256_html'],'sha256_metadados':r['sha256_metadados'],'fontes_publicas':r['fontes_publicas'],'tabelas_fonte':len(sp.structure),'objetos_visuais_fonte':sp.visual,'ocorrencias':contexts,'status':'alerta_contextual_nao_mascarado'};records.append(rec);proof.append(dict(rec,md_HEAD=raw.decode(),fonte_html_utf8=r['html_original'],metadados_raw=r['metadados_raw']))
 by[n]={'corpos':count,'com_placeholder':hits};print(n,by[n],flush=True)
p=BASE/'inventario_placeholders_publicados12669_v1.json';rp=BASE/'receipts_placeholders_publicados12669_v1.jsonl.gz';assert not p.exists() and not rp.exists();rp.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proof)+'\n').encode(),mtime=0));p.write_text(json.dumps({'HEAD':head,'resumo':by,'registros':records,'receipts':{'path':str(rp.relative_to(ROOT)),'sha256':sha(rp.read_bytes())},'limites':'Inventário lexical de todas as fontes integrais arquivadas dos dois pacotes, sem nova rede. Placeholder não é automaticamente lacuna normativa; requer contexto individual. Nenhuma alteração de canônico, guard ou máscara.'},ensure_ascii=False,indent=2)+'\n');print('TOTAL',len(records),flush=True)
