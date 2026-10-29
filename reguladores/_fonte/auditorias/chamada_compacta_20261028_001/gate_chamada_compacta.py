"""Alertas específicos de chamada de anexo concatenada; nunca emenda o corpo."""
import re,unicodedata

def chamadas(corpo):
 normalized=''.join(c for c in unicodedata.normalize('NFD',corpo.lower())if not unicodedata.combining(c));out=[]
 for m in re.finditer(r'\banex[oa]s?(?:dest[ae]|aest[ae])\s*(?:portaria|resolucao|instrucao(?:\s*normativa)?|decreto|ato)\b',normalized):
  out.append({'classe':'chamada_deitica_compacta_para_revisao','chamada_normalizada':m[0],'contexto_normalizado':normalized[max(0,m.start()-220):m.end()+400],'estado':'revisao_contextual_necessaria','ausencia_propria_demonstrada':False,'limites':'Literal concatenado específico exige confrontar objeto, citação e representação. Não prova ausência por si só; publicação prospectiva sem essa chamada não é equiparada a anexo próprio atual.'})
 return out
