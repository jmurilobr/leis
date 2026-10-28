"""Prova individual de escopo do PDF observado nos anexos da LOA SE8.963/2022.

Não converte PDF nem libera outros anexos. Os bytes originais são a representação.
"""
import hashlib,re,io
from pypdf import PdfReader

PDF_SHA='27fe6e1d5a7af0b5ba4fa5ef38c3a62c9ed161074c78d0f5348a415d1f66fc8c'
SEM_FOLIO={1:'Capa geral dos anexos',2:'Expediente institucional',3:'Índice parte1',4:'Índice parte2',5:'Capa do AnexoI',438:'Capa do AnexoII'}
def conferir_texto_paginas(pages):
 if len(pages)!=522:raise ValueError('PDF não fecha em522 páginas')
 if not re.search(r'LEI Nº 8[.]963, DE 13 DE JANEIRO DE 2022',' '.join(pages[0].split())):raise ValueError('capa não identifica lei/data')
 if 'ANEXO I' not in pages[4] or 'ANEXO II' not in pages[437]:raise ValueError('capas dos anexos não identificadas')
 rows=[]
 for n,text in enumerate(pages,1):
  visible=' '.join(text.split())
  if not visible:raise ValueError('página sem texto para qualificação de escopo')
  matches=list(re.finditer(r'(\d+)\s*\|\s*LOA\s*2022\s*-\s*Lei\s*N[º°]\s*([\d.]+)/2022',text,re.I))
  if n not in SEM_FOLIO:
   if len(matches)!=1 or int(matches[0][1])!=n or matches[0][2]!='8.963':raise ValueError('fólio/identidade de página divergente')
  elif matches:raise ValueError('estrutura das seis preliminares mudou')
  if n in [3,4,5,438] and not re.search(r'LEI Nº 8[.]963, DE 13 DE JANEIRO DE 2022',visible):raise ValueError('identidade preliminar diverge')
  rows.append(dict(pagina=n,sha256_texto=hashlib.sha256(text.encode()).hexdigest(),caracteres=len(text),folio=matches[0][0] if matches else None,sem_folio=SEM_FOLIO.get(n),inicio=visible[:240],fim=visible[-240:]))
 if not re.search(r'Quadro de Emenda Modificativa.*?255/2021.*?Orçamentária Anual de 2022',' '.join(pages[-1].split()),re.I):raise ValueError('fechamento não é quadro da proposta orçamentária2022')
 return rows

def conferir_pdf(blob,text):
 if hashlib.sha256(blob).hexdigest()!=PDF_SHA or len(blob)!=3831792:raise ValueError('PDF original diverge')
 if not blob.startswith(b'%PDF-') or not blob.rstrip().endswith(b'%%EOF'):raise ValueError('assinatura/fechamento PDF ausente')
 reader=PdfReader(io.BytesIO(blob),strict=True)
 if reader.is_encrypted or len(reader.pages)!=522 or int(reader.trailer['/Root']['/Pages']['/Count'])!=522:raise ValueError('árvore de páginas/encriptação inesperada')
 catalog=reader.trailer['/Root']
 if any(k in catalog for k in ['/OpenAction','/AA']) or '/JavaScript' in catalog.get('/Names',{}):raise ValueError('ação ativa exige revisão')
 pages=text.split('\f')
 if pages[-1]!='':raise ValueError('extração não terminou com separador completo de página')
 pages=pages[:-1];rows=conferir_texto_paginas(pages)
 return dict(total_paginas=522,folios_consecutivos=516,preliminares_sem_folio=SEM_FOLIO,paginas=rows,sha256_PDF=PDF_SHA,bytes=3831792,identidade='Lei8.963 de13/01/2022; LOA2022, anexosI/II',escopo='Livro orçamentário individual: capa/expediente/índices/capas de anexos e sequência1–522; páginas numeradas identificam a mesma lei. Referências a legislação nos quadros dos órgãos integram os anexos; nenhum ato vizinho identificado.',limite='Identidade/escopo e fechamento do arquivo; não certifica edição DOE. O PDF original completo é preservado, sem transcrever ou descartar curvas, gráficos, tabelas ou imagens.')
