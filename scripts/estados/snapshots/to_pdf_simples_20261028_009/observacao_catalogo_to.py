"""Preservar nota literal do cartão, sem confundi-la com edição ou vigência."""
import gzip,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from coletar_to_portal_indice import parse
SHA=lambda b:hashlib.sha256(b).hexdigest()
def observacao_catalogo(row):
    item=row['item']
    if not item.get('indicacao_editorial_compilacao'):return None
    idx=item['indice'];url=urlsplit(idx['url'])
    if idx.get('http')!=200 or url.scheme!='https' or url.hostname!='www.al.to.leg.br' or url.path!='/legislacaoEstadual':raise ValueError('índice oficial da nota não comprovado')
    packed=Path(idx['cache']).read_bytes();raw=gzip.decompress(packed)
    if SHA(packed)!=idx['sha256_cache'] or SHA(raw)!=idx['sha256_fonte']:raise ValueError('fonte da nota do catálogo diverge')
    _,rows,_=parse(raw);matches=[r for r in rows if r['fonte']==row['url']]
    if len(matches)!=1:raise ValueError('nota do cartão sem identidade única')
    obs=matches[0]
    for k in ['id_ALETO','titulo_indice','ementa','indicacao_editorial_compilacao']:
        if obs[k]!=item[k]:raise ValueError('nota selecionada diverge do cartão literal: '+k)
    return ('O cartão oficial ALETO registra literalmente na ementa: '+item['ementa']+
            ' A observação preserva informação do catálogo, sem afirmar que a mesma nota esteja no PDF. '
            'As anotações textuais efetivamente presentes no arquivo, quando existentes, estão preservadas no corpo e identificadas separadamente. '
            'Nenhuma situação jurídica atual foi inferida; situacao/revogada permanecem null.')
