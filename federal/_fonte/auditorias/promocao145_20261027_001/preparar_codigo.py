from pathlib import Path
B=Path(__file__).resolve().parent;A=B.parent/'promocao96_20261027_001';s=(A/'promover96.py').read_text().replace('promover96','promover145').replace('recibo96','recibo145').replace('promocao96','promocao145').replace('96','145').replace('41 + 16 + 39','113 + 31 + 1')
start=s.index('for package in receipt[\'pacotes\']:');end=s.index('assert len(allrows)==145;',start)
s=s[:start]+'''for package in receipt['pacotes']:
 manifest=read(safe(package['manifesto']))
 if package.get('reparo_6223'):
  r=manifest;archive=safe(r['fonte_prova']['path']);raw=archive.read_bytes();assert sha(raw)==r['fonte_prova']['sha256'];proof=read_gzip= json.loads(gzip.decompress(raw));source=proof['fonte_original_completa'];old=next(x for x in read(safe(package['preparo']))['registros'] if x['path']==r['path']);assert old['path']==r['path']
  assert sha(source['metadados_raw'].encode())==source['fila']['sha256_metadados_raw']
  for sourcefile in source['fontes_completas']:assert sha(base64.b64decode(sourcefile['bytes_originais_base64'],validate=True))==sourcefile['recibo']['sha256_raw']
  r={**old,**r,'sha256_candidato':r['sha256_final'],'area_normativa_html':r['HTML_normativo']};final=proof['candidato_final_utf8'].encode();assert sha(final)==r['sha256_candidato'] and safe(r['candidato']).read_bytes()==final;allrows.append((r,source,proof,final,False));provenance.extend([safe(package['manifesto']),archive]);continue
 rows=manifest['publicaveis_privados'];assert len(rows)==package['aprovados'];ref=manifest[package['campo_fontes']];archive=safe(ref['path']);raw=archive.read_bytes();assert sha(raw)==ref['sha256'] and len(raw)<95*1024**2;proofs=[json.loads(x) for x in gzip.decompress(raw).splitlines()];assert len(proofs)==package['fontes'];records={}
 for proof in proofs:
  source=proof['fontes_completas_anteriores'] if package['revisao_individual'] else proof
  path=source['fila']['path'];assert path not in records;records[path]=(proof,source)
  assert sha(source['metadados_raw'].encode())==source['fila']['sha256_metadados_raw']
  for sourcefile in source['fontes_completas']:assert sha(base64.b64decode(sourcefile['bytes_originais_base64'],validate=True))==sourcefile['recibo']['sha256_raw']
 for r in rows:
  proof,source=records[r['path']];assert proof['candidato_aprovado']==r;assert proof['replay']['aprovado'] is True
  final=proof['md_final_utf8'].encode();assert sha(final)==r['sha256_candidato'] and safe(r['candidato']).read_bytes()==final
  allrows.append((r,source,proof,final,package['revisao_individual']))
 provenance.extend([safe(package['manifesto']),archive])
''' + s[end:]
s=s.replace(';assert payload.strip()', ';assert payload.strip()')
s=s.replace("assert payload.strip()==expected.strip(),'Corpo candidato diverge da conversão integral congelada'",'''if path==receipt['reparo6223']['path']:
  assert sha(raw)==receipt['reparo6223']['sha256_final'];assert len(re.findall(r'^1\\) De uma para outra',expected,re.M))==1
  expected=re.sub(r'^1\\) De uma para outra',lambda m:r'1\\) De uma para outra',expected,flags=re.M)
 assert payload.strip()==expected.strip(),'Corpo candidato diverge da conversão integral congelada' ''')
s=s.replace("assert 'RESOLVE' in normal(v.texto_visivel_html(body_html)) and 'GETULIO VARGAS' in normal(v.texto_visivel_html(body_html))", "assert re.search(r'\\b(?:RESOLVE|DECRETA)\\b',normal(v.texto_visivel_html(body_html))) and 'GETULIO VARGAS' in normal(v.texto_visivel_html(body_html))")
s=s.replace("assert len(allrows)==145;",'''# Every selected candidate is bound to the independent contextual boundary inventory.
boundary=read(safe(receipt['diagnostico241']));by_path={r['path']:r for r in boundary['registros'] if r['estado_corpus']=='privado'}
for r,source,proof,raw,individual in allrows:
 br=by_path[r['path']];assert br['sha256_MD_candidato_fechado']==sha(raw);assert br['sha256_area_normativa_HTML']==sha(r['area_normativa_html'].encode())
 assert not br['fecho_antes_primeiro_artigo_e_assinatura_presidencial'] and not br['separacoes_principal_documento_possiveis']
 if br['comando_explicito_antes_artigos']:assert r['path']==receipt['contexto6107']['path'] and sha(raw)==receipt['contexto6107']['sha256_liberado_ROOT']
assert len(allrows)==145;''')
s=s.replace(";if path==receipt['reparo6223']['path']:","\n if path==receipt['reparo6223']['path']:")
(B/'promover145.py').write_text(s)
