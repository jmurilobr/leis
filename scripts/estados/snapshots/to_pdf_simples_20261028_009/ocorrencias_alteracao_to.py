"""Ocorrências literais: forma textual observada, sem decidir sua natureza jurídica."""
from edicao_anotada_to import EDITORIAL,EXTRA,INICIO

def conferir_ocorrencias(text):
    out=dict(anotacoes_editoriais=[],referencias_alteracao_textuais=[])
    spans=sorted({(m.start(),m.end()) for pattern in [EDITORIAL,EXTRA] for m in pattern.finditer(text)})
    seen=set()
    for start,end in spans:
        left=text.rfind('\n',0,start)+1;right=text.find('\n',end)
        if right<0:right=len(text)
        if left in seen:continue
        seen.add(left);literal=text[left:right];prefix=text[left:start]
        delimited=not prefix.strip().strip('*“\"\' (') and bool(INICIO.match(literal))
        row=dict(linha_inicial=text.count('\n',0,left)+1,trecho_literal=literal,contexto_literal=text[max(0,left-120):min(len(text),right+240)])
        if delimited:out['anotacoes_editoriais'].append(row)
        else:
            row['natureza_juridica_nao_classificada']=True
            out['referencias_alteracao_textuais'].append(row)
    return out
