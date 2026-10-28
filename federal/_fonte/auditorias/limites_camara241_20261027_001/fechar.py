from pathlib import Path
import json,hashlib,re,gzip,sys
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'scripts'));import baixar_federal as f
from identidade_decreto_revisao import normal
from estados.pe_fidelidade_visivel import texto_visivel_html
sha=lambda x:hashlib.sha256(x).hexdigest()
d=json.loads((B/'inventario241.json').read_text());rows=[]
for p in ['alimentacao_20261027_006/revisao_sem_artigos001/lote_revisao35_v2.json','alimentacao_20261027_007/lote_camara200.json']:
 rows+=json.loads((B.parent/p).read_text())['publicaveis_privados']
p=B.parent/'alimentacao_20261027_006/reparo6223_001/manifesto6223_v2.json';x=json.loads(p.read_text());rows.append({**x,'sha256_candidato':x['sha256_final']});assert len(rows)==145
held='federal/decretos/1940/dec-6107-1940-08-15.md';selected=[r for r in rows if r['path']!=held];assert len(selected)==144
# Supplemental scanner examines physical line starts as well as paragraph starts.
# This prevents DECRETA + hard break + Artigo único being mistaken for no article.
checks=[]
for r in rows:
 area=r.get('area_normativa_html') or r['HTML_normativo'];blocks=f.convert(area).split('\n\n');matches=[]
 for i,b in enumerate(blocks):
  for line in b.splitlines():
   n=normal(texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',line)))
   if re.match(r'^(?:ARTIGO|ART\.?)\s*[.º°O]*\s*(?:\d+(?:[.º°O]|\b)|UNICO\b)',n):matches.append({'bloco_indice':i,'linha_literal':line})
 checks.append({'path':r['path'],'sha256_MD':r['sha256_candidato'],'artigos_por_inicio_de_linha':matches,'sem_artigo_reconhecido':not matches})
(B/'suplemento_linhas145.json').write_text(json.dumps({'motivo':'Artigo único pode compartilhar bloco com DECRETA por quebra HTML. Scanner complementar, sem alterar a prova original.','registros':checks},ensure_ascii=False,indent=2)+'\n')
assert sum(c['sem_artigo_reconhecido'] for c in checks)==31
result={'estado':'Seleção privada sucessora, sem promoção; 6.107 separado até leitura ROOT.','HEAD_auditado':d['HEAD'],'resumo':{'publicados_auditados':96,'privados_originais':145,'selecionados':144,'separados_para_leitura':1,'novas_pendencias_propostas_publicados':0,'alteracoes_canônicas':0},'insumos_originais':d['insumos'],'limite':'Revisão contextual do defeito de deslocamento de fecho principal para documento incorporado. Não substitui os demais gates nem afirma revisão humana universal. Os 96 possuem SHA real do HEAD no inventário.','publicaveis_privados':selected,'separados':[r for r in rows if r['path']==held],'interpretacao6107':'Alerta lexical contextualizado: autorizada a funcionar pelos Decretos está no preâmbulo histórico; não é comando novo anterior a documento incorporado. O Artigo único e o único fecho são próprios. Mantido separado até ROOT ler.','preservacao':'Nenhum manifesto, candidato ou lista anterior modificado.'}
(B/'selecao_sucessora144.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(B/'selecionados144-paths.txt').write_text(''.join(r['path']+'\n' for r in selected));(B/'candidatos144-paths.txt').write_text(''.join(r['candidato']+'\n' for r in selected));
summary={'resumo':result['resumo'],'HEAD':d['HEAD'],'fonte6107':d['casos_para_revisao'][0],'provas6107_sha256':sha((B/'provas_casos241.jsonl.gz').read_bytes()),'publicados96_SHA_reais':[{'path':r['path'],'OID':r['OID_HEAD_real'],'sha256':r['sha256_MD_HEAD_real']} for r in d['registros'] if r['estado_corpus']=='publicado'],'controles_linhas':'Os três artigos únicos unidos a DECRETA no mesmo bloco são reconhecidos no suplemento; os 31 comandos sem artigos são os já contextualizados no pacote revisão35.','limitacoes':result['limite']}
(B/'recibo_fechamento.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
paths=sorted(p for p in B.iterdir() if p.is_file() and p.name not in ['entrega-paths.txt','entrega-hashes.json']);assert all(sha((R/r['candidato']).read_bytes())==r['sha256_candidato'] for r in rows)
(B/'entrega-paths.txt').write_text(''.join(str(p.relative_to(R))+'\n' for p in paths));(B/'entrega-hashes.json').write_text(json.dumps([{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in paths],ensure_ascii=False,indent=2)+'\n');print(result['resumo']);print('Entrega',len(paths))
