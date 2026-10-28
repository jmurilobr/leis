"""Edição CLBR privada integral, sem promover ou alterar transcrição anterior."""
from pathlib import Path
import hashlib,json,gzip,subprocess,re,struct,datetime
from zoneinfo import ZoneInfo
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest()
def info(p):return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def save(n,o):
 p=B/n;assert not p.exists();p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');return p
canonical='federal/decretos/1945/dec-18351-1945-04-11.md';head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();old=subprocess.check_output(['git','show',head+':'+canonical],cwd=R);assert old==(R/canonical).read_bytes()
prior=json.loads((R/'federal/_fonte/auditorias/inventario_tecnico_HEAD_20261027_009/leitura_dirigida8.json').read_bytes());record=next(r for r in prior['registros'] if r['path']==canonical);assert sha(old)==record['sha256_MD_HEAD_real']
p=B/'preimagem_HEAD18351.md';assert not p.exists();p.write_bytes(old)
pdf=R/'federal/_fonte/auditorias/clbr_1945_recuperacao_20261027_001/1945-decretos.pdf';pdfsha=sha(pdf.read_bytes());assert pdfsha=='29553bac45833de9cdcefbe5eda0c8f0c57b55b6d3bf4f9739346d3475c39c6f'
capture=R/'federal/_fonte/auditorias/clbr_1945_recuperacao_20261027_001/recibo1945.json';cap=json.loads(capture.read_bytes());date=datetime.datetime.fromisoformat(cap['captura_inicio_utc']).astimezone(ZoneInfo('America/Recife')).date().isoformat();assert date=='2026-10-27'
urn='urn:lex:br:federal:decreto:1945-04-11;18351';expected=re.search(r'(?m)^sha256_metadados_fonte: "([a-f0-9]+)"',old.decode())[1];mp=R/'federal/_fonte/metadados-normas'/sha(urn.encode());metaraw=next(raw for f in mp.glob('*.json.gz') if sha(raw:=gzip.decompress(f.read_bytes()))==expected);meta=json.loads(metaraw);assert meta['legislationIdentifier']==urn and meta['legislationDate']=='1945-04-11';assert any(e.get('version')=='Original' and re.search(r'vol\.\s+004',e.get('name','')) for e in meta['encoding'])
hpath=R/'federal/_fonte/decretos/1945/dec-18351-1945-04-11.html.gz';htmlraw=gzip.decompress(hpath.read_bytes());assert sha(htmlraw)==record['sha256_HTML']
history=B/'preimagens_normas18351.json.gz';assert not history.exists();history.write_bytes(gzip.compress(json.dumps({'MD_HEAD_utf8':old.decode(),'HTML_cache_utf8':htmlraw.decode(),'metadados_raw':metaraw.decode(),'origem':'Arquivos preexistentes; autoria ou nova captura não presumidas.','sha256_HTML':sha(htmlraw),'sha256_API':sha(metaraw),'fonte_API':'https://normas.leg.br/api/public/normas?urn='+urn+'&tipo_documento=maior-detalhe'},ensure_ascii=False).encode(),mtime=0))
mapping={132:1082,133:1083,134:1089,135:1090,136:1091,137:1092,138:1093,139:1084,140:1085,141:1086,142:1087,143:1088,144:1100,145:1101,146:1102,147:1103,148:1094,149:1095,150:1096,151:1097,152:1098,153:1099}
labels={139:'Figura 1: blusão, frente',140:'Figura 1a: blusão com equipamento',141:'Figura 1b: blusão, costas',142:'Figura 2: calça',143:'Figura 3: capa, gola abaixada',144:'Figura 3a: capa, gola levantada',145:'Figura 3b: capa, costas',146:'Figura 4: distintivo Brasil',147:'Figura 5: gorro, aba levantada',148:'Figura 5a: gorro, aba abaixada',149:'Figura 6: macacão',150:'Figura 7: mala, parte interna',151:'Figura 7a: mala, duas bolsas',152:'Figura 7b: mala, bolsa e cartão',153:'Figura 8: mosquiteiro'}
assets=[]
for pn,pdfn in mapping.items():
 image=B/'render300'/('dec18351-p132-proprio.png' if pn==132 else f'dec18351-{pdfn}.png');data=image.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n');w,h=struct.unpack('>II',data[16:24]);dest=f'federal/anexos/decretos/1945/dec-18351-1945-04-11-clbr-p{pn}.png';assert not (R/dest).exists();assets.append({**info(image),'destino':dest,'pagina_impressa':pn,'pagina_PDF':pdfn,'largura':w,'altura':h,'dpi':300,'rotulo':labels.get(pn,'Corpo e tabelas do ato'),'recorte':{'x':0,'y':670,'W':w,'H':h,'criterio':'Exclui somente a parte final do decreto anterior acima da epígrafe própria.'} if pn==132 else None})
assert len(assets)==22 and len(labels)==15 and sorted(mapping)==list(range(132,154))
note=('Edição CLBR de 1945, seção volume IV, páginas 132–153, em fac-símile integral: decreto, plano, tabelas 1 e 2 e quinze folhas com figuras 1–8 e variantes. '
      'As páginas estão apresentadas na ordem impressa; a ordem digital do PDF é diferente em parte das folhas, conforme mapa preservado. '
      'O artigo 1º impresso inclui suboficiais, palavra ausente no principal da transcrição anterior do Normas. Para preservar uma edição coerente, não se mesclaram o corpo anterior e figuras da CLBR. '
      'A versão anterior foi arquivada integralmente, sem emenda. O índice da CLBR identifica 18.351, de 11/04/1945, página 132, e informa publicação no Diário Oficial de 26/04/1945. '
      'O PDF anual foi capturado em 27/10/2026 no fuso America/Recife; a preparação desta reprodução ocorreu em 28/10. Não se infere vigência pela reprodução.')
header=old.decode().split('---\n',2)[1].rstrip();lines=[]
for line in header.splitlines():
 if line.startswith('fonte:'):line='fonte: '+json.dumps(cap['url_primaria_observada'])
 elif line.startswith('baixado_em:'):line='baixado_em: '+date
 elif line.startswith('versao_texto:'):line='versao_texto: "edição CLBR original integral em fac-símile"'
 lines.append(line)
lines+=['sha256_pdf_fonte: '+json.dumps(pdfsha),'fonte_texto_anterior: '+json.dumps('https://normas.leg.br/?urn='+urn),'nota_editorial_fonte: '+json.dumps(note,ensure_ascii=False)]
body='\n# Decreto nº 18.351 de 11/04/1945\n\nEdição CLBR de 1945, volume IV. Decreto, plano, tabelas e figuras em fac-símile.\n\n'
for a in assets:
 label=f"Página {a['pagina_impressa']} — {a['rotulo']}";body+='### '+label+'\n\n!['+label+'](../../anexos/decretos/1945/'+Path(a['destino']).name+')\n\n'
candidate=B/'dec-18351-1945-04-11-clbr-integral.md';assert not candidate.exists();candidate.write_text('---\n'+'\n'.join(lines)+'\n---\n'+body.rstrip()+'\n');assert candidate.read_text().count('![')==22
proofs=[B/'render/capa_IV.png',B/'render/indice_18351_pXIV.png',B/'render/final18351-1104.png',B/'render/ato18351-1082.png']
manifest=save('candidato18351.json',{'estado':'Privado para revisão/promoção exclusiva ROOT; nenhum canônico, Git ou registro alterado.','HEAD_preimagem':head,'path_canonico':canonical,'preimagem':info(p),'candidato':info(candidate),'urn':urn,'identidade_API':{'sha256_raw':sha(metaraw),'data':meta['legislationDate'],'encoding_original_CLBR':meta['encoding']},'fonte_PDF_anual':info(pdf),'recibo_captura':info(capture),'baixado_em_local':date,'preparado_em_local':datetime.datetime.now(ZoneInfo('America/Recife')).isoformat(),'ativos_em_ordem_impressa':assets,'historia_normas':info(history),'provas_bibliograficas_e_limites':[info(p) for p in proofs],'nota_editorial':note,'conferencia_visual':'Inspeção individual das páginas em renders de 110 dpi, incluindo sete páginas de texto/tabelas e quinze folhas ilustradas; recorte próprio da primeira página também visto em 300 dpi. Arquivos normativos são renders diretos em 300 dpi, sem edição, reconstrução ou melhora de pixels. Página 154 já inicia o decreto 18.352 e foi excluída do corpo.','limites':'Fac-símile, não transcrição textual pesquisável. Figuras fotográficas têm contraste limitado na digitalização original; não foram recriadas. ROOT ainda revisará os arquivos finais. Não certifica vigência nem ausência de outras versões.'})
files=[Path(__file__).resolve(),p,candidate,manifest,history,pdf,capture]+[R/a['path'] for a in assets]+proofs
lp=B/'entrega18351-paths.txt';assert not lp.exists();lp.write_text(''.join(str(p.relative_to(R))+'\n' for p in files));save('entrega18351-hashes.json',[info(p) for p in files+[lp]])
print(json.dumps({'ativos':len(assets),'figuras':15,'arquivos':len(files),'sha256_candidato':sha(candidate.read_bytes()),'bytes_imagens':sum(a['bytes'] for a in assets),'preimagem_SHA256':sha(old),'HEAD':head},ensure_ascii=False))
