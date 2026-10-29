"""Alerta conservador de órgão: não infere cadeia corrigida nem altera texto."""
import re,unicodedata

def n(s):return ' '.join(''.join(c for c in unicodedata.normalize('NFD',str(s).lower())if not unicodedata.combining(c)).split())
ROOT=re.compile(r'^(?:ministerio|presidencia|atos do poder|entidades de fiscalizacao|conselho|defensoria|senado|camara|supremo|tribunal|justica|procuradoria|agencia|instituto|secretaria|departamento|fundacao|universidade|comando|banco)\b')
NOTICE=re.compile(r'edicoes eletronicas.{0,100}diario oficial|certificad.{0,100}icp.brasil|produzem.{0,80}mesmos efeitos legais')
GOAL=re.compile(r'^[·•\s]*[0-9A-Z]{4}\s*[-–—]\s*(?:aumentar|qualificar|promover|reduzir|implanta|amplia)',re.I)

def motivos(orgao,orgao_html,corpo):
 reasons=[]
 if not isinstance(orgao,str)or not orgao.strip():return ['Órgão ausente no metadado']
 if not isinstance(orgao_html,str)or not orgao_html.strip():return ['Órgão ausente no campo primário']
 a=[p.strip()for p in orgao.split('/')];b=[p.strip()for p in orgao_html.split('/')]
 if a!=b:reasons.append('Cadeia do MD diverge do campo primário')
 if not all(a):reasons.append('Nível vazio na cadeia de órgão')
 if not ROOT.search(n(a[0])):reasons.append('Raiz não identificada como instituição; exige contexto')
 for p in a:
  v=n(p)
  if NOTICE.search(v):reasons.append('Aviso editorial de edição/certificação no campo de órgão')
  if GOAL.search(p)or '%'in p:reasons.append('Meta física/percentual no campo de órgão')
  if re.search(r'\binserir (?:imagens?|tabelas?|quadros?)\b',v):reasons.append('Comando editorial de inserção no campo de órgão')
  if re.match(r'^sessao plenaria\b',v):reasons.append('Evento/sessão informado como nível institucional; exige contexto')
 if NOTICE.search(n(corpo))or re.search(r'\b048h\s*[-–—].{0,50}aumentar a proporcao',n(corpo)):reasons.append('Expressão de aviso/meta no corpo exige leitura contextual; não removida')
 return list(dict.fromkeys(reasons))
