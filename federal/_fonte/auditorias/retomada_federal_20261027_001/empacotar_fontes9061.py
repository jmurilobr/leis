from pathlib import Path
import json,sys,gzip,hashlib,collections
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();rows=json.loads((BASE/'verificacao_9061.json').read_text())['registros'];prom={r['path']:r for r in json.loads((BASE/'promocoes_395.json').read_text())['substituicoes']};ms={}
for no,ver in [(15,4),(16,4),(17,4),(18,4),(19,3)]:
 for r in json.loads((ROOT/f'federal/_lote_dec_continuacao_20261020_{no:03}_v{ver}.json').read_text())['publicaveis']:ms[r['path']]=r
D=BASE/'fontes9061';D.mkdir(exist_ok=False);target=40*1024**2;hard=95*1024**2;part=0;size=0;fh=None;mapping=[];parts=[]
def close():
 global fh
 if fh:
  fh.close();raw=fp.read_bytes();assert len(raw)<hard;parts.append({'path':str(fp.relative_to(ROOT)),'sha256_gzip':sha(raw),'bytes_gzip':len(raw),'registros':sum(r['parte']==part for r in mapping)});fh=None
for i,r in enumerate(rows,1):
 p=r['path'];m=ms[p];final=(ROOT/r['arquivo_final']).read_bytes();html=gzip.decompress((ROOT/r['fonte_html_cache']).read_bytes());api=gzip.decompress((ROOT/r['captura_metadados']).read_bytes());assert sha(final)==r['sha256_md_final'] and sha(html)==r['sha256_html'] and sha(api)==r['sha256_metadados'];before=(ROOT/p).read_bytes() if p in prom else None
 if before is not None:assert sha(before)==prom[p]['sha256_preimagem']
 obj={'path':p,'urn':r['urn'],'numero':r['numero'],'data':r['data'],'fontes_publicas':{'pagina':m['fonte'],'texto':m['url_texto'],'metadados':'https://normas.leg.br/api/public/normas?urn='+r['urn']+'&tipo_documento=maior-detalhe'},'paths_originais':{'md_final':r['arquivo_final'],'html':r['fonte_html_cache'],'metadados':r['captura_metadados']},'sha256_md_final':sha(final),'sha256_html':sha(html),'sha256_metadados':sha(api),'sha256_preimagem':sha(before) if before is not None else None,'md_final':final.decode(),'html_original':html.decode(),'metadados_raw':api.decode(),'md_preimagem':before.decode() if before is not None else None};raw=(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n').encode();member=gzip.compress(raw,compresslevel=6,mtime=0);assert len(member)<hard
 if fh is None or (size+len(member)>target and size):
  close();part+=1;fp=D/f'fontes9061_parte{part:03}.jsonl.gz';assert not fp.exists();fh=fp.open('wb');size=0
 offset=size;fh.write(member);size+=len(member);mapping.append({'path':p,'urn':r['urn'],'parte':part,'arquivo':str(fp.relative_to(ROOT)),'offset_gzip':offset,'bytes_gzip_member':len(member),'sha256_member_gzip':sha(member),'sha256_registro_jsonl':sha(raw),'sha256_md_final':sha(final),'sha256_html':sha(html),'sha256_metadados':sha(api),'sha256_preimagem':obj['sha256_preimagem']})
 if i%2000==0:print('fontes',i,'/',len(rows),'parte',part,flush=True)
close();assert len(mapping)==9061 and sum(r['sha256_preimagem'] is not None for r in mapping)==395
res={'escopo':'Fontes públicas integrais HTML/API, MD final dos 9.061 e preimagem dos 395 candidatos. Cada linha JSON é um membro gzip independente; concatenação gzip padrão preserva todos os registros. Sem cabeçalhos de sessão ou cookies.','alvo_parte_bytes_gzip':target,'limite_duro_parte_bytes_gzip':hard,'resumo':{'normas':len(mapping),'preimagens':395,'partes':len(parts),'bytes_gzip_total':sum(p['bytes_gzip'] for p in parts)},'partes':parts,'registros':mapping};p=D/'mapa_fontes9061.json';p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['resumo'])
