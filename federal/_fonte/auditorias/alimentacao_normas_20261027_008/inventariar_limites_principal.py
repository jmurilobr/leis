from pathlib import Path
import json,re,hashlib,sys
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'));import baixar_federal as f
from identidade_decreto_revisao import normal,FECHO,MESES
from estados.pe_fidelidade_visivel import texto_visivel_html
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((B/'pacote_final001/lote_final.json').read_bytes());prep={r['path']:r for r in json.loads((B/'qa_final_v3/preparo.json').read_bytes())['registros']};out=[];datepat=r'(?:RIO DE JANEIRO|BRASILIA)[,.;\s]+(?:EM\s*)?(?:DE\s*)?\d{1,2}[º°]?\s*(?:DE\s*)?[A-Z]+\s*[,;]?\s*(?:DE\s*)?[12]\.?\d{3}';artpat=r'^(?:ARTIGO|ART\.?)\s*[.º°O]*\s*(?:\d+(?:[.º°O]|\b)|UNICO\b)'
for row in m['publicaveis_privados']:
 r=prep[row['path']];body=f.convert(r['HTML_normativo_normalizado']);blocks=body.split('\n\n');first=next((i for i,b in enumerate(blocks) if re.match(artpat,normal(texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',b))))),None);assert first is not None;prefix=blocks[:first];dates=[]
 for i,b in enumerate(prefix):
  n=normal(texto_visivel_html(b))
  if re.match(r'^(?:RIO DE JANEIRO|BRASILIA)\b',n):
   for x in re.finditer(datepat,n):dates.append({'bloco_indice':i,'bloco_literal':b,'data_literal_normalizada':x[0]})
 if dates:out.append({'path':row['path'],'urn':row['urn'],'sha256_md_final':row['sha256_candidato'],'sha256_html':row['sha256_html'],'epigrafe':row['epigrafe'],'fecho_qualificado_anterior':row['fecho_principal'],'prefixo_antes_primeiro_artigo_reconhecido':'\n\n'.join(prefix),'primeiro_artigo_reconhecido':blocks[first],'fechos_antes_primeiro_artigo':dates,'estado':'Revisão documental de comando principal sem artigos ou documento incorporado; não liberar pelo artigo do objeto aprovado.'})
p=B/'inventario_principal_incorporados467_v2.json';assert not p.exists();p.write_text(json.dumps({'escopo':'Inventário somente leitura dos467 candidatos: fecho literal antes do primeiro bloco de artigo reconhecido. Não infere ausência só por regex; fornece contexto completo do prefixo e do primeiro artigo.','candidatos_examinados':len(m['publicaveis_privados']),'casos_para_revisao':len(out),'registros':out},ensure_ascii=False,indent=2)+'\n');print('Casos com fecho antes do primeiro artigo:',len(out));print([r['path'] for r in out])
