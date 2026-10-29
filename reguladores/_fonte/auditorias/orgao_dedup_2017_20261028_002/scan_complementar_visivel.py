from pathlib import Path
import sys,json,gzip,hashlib,re,html,collections
R=Path.cwd();D=Path(__file__).resolve().parent;sys.path[:0]=[str(D/'codigo')];from gate_orgao import motivos
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'manifesto5769.json').read_bytes());expected={r['path']:r for r in m['documentos']};out=[];checked=0
for part in m['primarias_partes']:
 with gzip.open(R/part['path'],'rt')as f:
  for line in f:
   p=json.loads(line)
   if p['path']not in expected:continue
   checked+=1;src=p['HTML_utf8'];fragment=re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)',src,re.S)[0];plain=html.unescape(re.sub(r'<[^>]+>',' ',fragment));org=expected[p['path']]['meta']['orgao'];why=motivos(org,org,plain);private=[{'caractere':c,'codepoint':'U+%04X'%ord(c),'contexto':plain[max(0,k-100):k+100]}for k,c in enumerate(plain)if'\ue000'<=c<='\uf8ff'];css=[block for block in re.findall(r'<style\b[^>]*>(.*?)</style>',src,re.S|re.I)if re.search(r'counter-(?:reset|increment)|\bcontent\s*:',block,re.I)]
   if why or private or css:out.append({'path':p['path'],'sha256_MD':p['sha256_md'],'sha256_HTML':p['sha256_fonte'],'alertas_apos_entidades_HTML':why,'PUA':private,'CSS_com_conteudo_gerado_para_contexto':css})
assert checked==5769;o={'fontes_examinadas':checked,'alertas':out,'limites':'Triagem complementar de entidades HTML, caracteres PUA e CSS de conteúdo gerado fornecido no snapshot; não executa estilos externos ou afirma identidade visual.'};(D/'scan_complementar_visivel.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print('Fontes',checked,'alertas',len(out));print([(r['path'],r['alertas_apos_entidades_HTML'],r['PUA'][:1],bool(r['CSS_com_conteudo_gerado_para_contexto']))for r in out][:20])
