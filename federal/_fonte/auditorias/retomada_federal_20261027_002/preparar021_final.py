from pathlib import Path
import json,sys,re,gzip,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));from preparar_lote_decretos_cache import fields
sha=lambda b:hashlib.sha256(b).hexdigest();B=ROOT/'federal';old=json.loads((B/'_lote_dec_continuacao_20261020_021.json').read_text());holds=json.loads((B/'_overlay_contexto_integridade_021_20261027_001.json').read_text())['registros'];hp={r['path'] for r in holds};notes={r['path']:r for r in json.loads((B/'_fechos_contextuais_20261027_022.json').read_text())['registros'] if r['status']=='candidato_privado_com_nota_literal_sem_emenda'};audit=json.loads((B/'_auditoria_pontuacao_federal_20261020_021_v1.json').read_text());proofs={r['path']:r for r in audit['auditados']+audit['divergencias_para_revisao']};D=B/'_candidatos_commonmark_021_20261027_001';D.mkdir(exist_ok=False);rows=[];changes=[];render=[]
for oldrow in old['publicaveis']:
 p=oldrow['path']
 if p in hp:continue
 r=dict(oldrow);canonical=(ROOT/p).read_bytes();assert sha(canonical)==r['sha256'];cp=notes[p]['candidato'] if p in notes else p;raw=(ROOT/cp).read_bytes();meta,cab,body=fields(raw.decode());n=r['epigrafe']['numero'];modified=body;why=[];native=n=='12418'
 if n in ['11242','10815','10818','10820','10662','10612']:
  num='2' if n=='11242' else '1';a='**Art. '+num+'º**';b='**Art.'+num+'º**';assert modified.count(a)==1;modified=modified.replace(a,b);why.append({'antes':a,'depois':b})
 elif n=='10790':
  pattern=r'(?m)^---------------------------$';assert len(re.findall(pattern,modified))==1;modified=re.sub(pattern,lambda m:'\\'+m[0],modified);why.append({'mudanca':'Escape somente do primeiro hífen para conservar literalmente os 27 hifens da fonte, sem convertê-los em regra horizontal.'})
 elif native:
  pr=proofs[p];src=gzip.decompress((ROOT/pr['fonte_html_cache']).read_bytes()).decode();assert sha(src.encode())==r['sha256_fonte_html'];norm=src;ad=pr['marcador_administrativo_excluido'];cuts=ad['paragrafos'] if ad else []
  for c in sorted(cuts,key=lambda c:c['inicio'],reverse=True):assert src[c['inicio']:c['fim']]==c['paragrafo_html'];norm=norm[:c['inicio']]+c['prefixo_literal_preservado']+c['sufixo_literal_preservado']+norm[c['fim']:]
  inner=re.search(r'<body\b[^>]*>([\s\S]*?)</body\s*>',norm,re.I);assert inner;h1=body.lstrip().partition('\n')[0];modified=h1+'\n\n'+inner[1].strip()+'\n';why.append({'mudanca':'Body HTML original integral, preservando ol type=A da assinatura sem perder a inicial A. Não altera texto, atributos ou listas da fonte.'})
 if modified!=body:
  new=('---\n'+cab.rstrip('\n')+'\n---\n'+modified).encode();cp=str((D/Path(p).name).relative_to(ROOT));(ROOT/cp).write_bytes(new);raw=new;changes.append({'path':p,'candidato':cp,'sha256_candidato':sha(raw),'sha256_preimagem':sha(canonical),'preimagem_privada':notes[p]['candidato'] if p in notes else p,'mudancas':why,'HTML_original':native})
 r.update(arquivo_final=cp,sha256_preimagem=sha(canonical),sha256=sha(raw),HTML_original=native,proof=proofs[p]);rows.append(r);render.append({'path':p,'markdown':fields(raw.decode())[2].lstrip().partition('\n')[2]})
assert len(rows)==1790 and len(changes)==8
(BASE/'preparo021_final.json').write_text(json.dumps({'publicaveis':rows,'retidos':old['retidos']+holds,'reparos_novos':changes,'notas_preexistentes':len(notes)},ensure_ascii=False,indent=2)+'\n');(BASE/'render021_final_input.json').write_text(json.dumps(render));print('corpos',len(rows),'reparos',len(changes),'notas preexistentes',len(notes))
