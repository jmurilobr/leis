"""Retenção contextual adicional; não infere órgão corrigido nem altera fontes."""
import re
from gate_orgao import n

def motivos(orgao,prefixo_autoridade):
 levels=[n(x)for x in str(orgao).split('/')];ministries=[p for p in levels if re.match(r'^ministerio\b',p)];out=[]
 if len(set(ministries))>1:out.append('Mais de um ministério distinto na cadeia hierárquica primária; revisão do vínculo, sem corrigir por inferência')
 if levels and levels[0]in {'ministerio do desenvolvimento social','ministerio do desenvolvimento social e agrario'}and any(x=='secretaria de comercio exterior'for x in levels[1:]):
  prefix=n(prefixo_autoridade)
  if re.search(r'\bo\s*secretario\s*de\s*comercio\s*exterior\s*[,;]?\s*do\s*ministerio\s*da\s*industria\s*[,;]?\s*comercio\s*exterior\s*e\s*servicos',prefix):out.append('Autoridade própria declara Ministério da Indústria, Comércio Exterior e Serviços, divergindo da raiz Desenvolvimento Social da cadeia primária')
 return out
