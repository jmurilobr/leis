"""Predicado conservador congelado; só delimita avaliação, nunca remove corpo."""
def principal_fechos(body):
 """Conservador: não empresta artigos ou fechos de documento incorporado."""
 seen_article=False;closings=[];boundary=None
 date_pattern=r'(?:RIO DE JANEIRO|BRASILIA)[,.;\s]+(?:EM\s*)?(?:DE\s*)?\d{1,2}[º°]?\s*(?:DE\s*)?[A-Z]+\s*[,;]?\s*(?:DE\s*)?[12]\.?\d{3}'
 article_pattern=r'^(?:ARTIGO|ART\.?)\s*[.º°O]*\s*(?:\d+(?:[.º°O]|\b)|UNICO\b)'
 header_pattern=r'^(?:ANEXOS?|REGULAMENTOS?|REGIMENTOS?|CONVENCOES|CONVENCAO|ESTATUTOS?|ACORDOS?|TABELAS?|RELACOES|RELACAO|INSTRUCOES|MODELOS?|RETIFICACAO|RETIFICACOES)\b'
 for block in body.split('\n\n'):
  text=normal(v.texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',block)))
  line_articles=any(re.match(article_pattern,normal(v.texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',line)))) for line in block.splitlines())
  if re.match(header_pattern,text):
   boundary={'bloco_literal':block,'cabecalho_normalizado':text,'artigo_principal_visto':seen_article};break
  if line_articles:seen_article=True
  matches=list(re.finditer(date_pattern,text))
  if matches and not seen_article and re.match(r'^(?:RIO DE JANEIRO|BRASILIA)\b',text):
   return [],{'bloco_literal':block,'motivo':'Fecho antes de qualquer artigo próprio; exige revisão específica do comando principal sem artigos, sem emprestar artigos posteriores.'}
  if not seen_article:continue
  for match in matches:
   found=FECHO.match(match[0]);assert found
   closings.append({'literal_normalizado':match[0],'data':datetime.date(int(found['ano'].replace('.','')),MESES[found['mes']],int(found['dia'])).isoformat(),'bloco_literal':block})
 return closings,boundary
