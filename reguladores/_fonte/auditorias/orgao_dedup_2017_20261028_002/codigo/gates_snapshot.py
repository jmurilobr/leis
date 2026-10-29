import re,html
from comum import normalizar_chave
def chave(meta, path):
    data = str(meta.get('data', ''))
    numero = re.sub('[.\\s]', '', str(meta.get('numero', '')).lower()).lstrip('0')
    if data:
        numero = re.sub('/' + re.escape(data[:4]) + '$', '', numero)
    return (path.split('/')[1], normalizar_chave(str(meta.get('tipo', ''))), numero, data)

def motivos_identidade(meta, path, keys, urls, tracked):
    k = chave(meta, path)
    if not all(k):
        return [{'motivo': 'identidade numérica incompleta exige qualificação pela epígrafe'}]
    if path in tracked or meta['fonte'] in urls or keys.get(k):
        return [{'motivo': 'identidade/URL/path coincidente; revisar subunidades', 'coincidencias': keys.get(k, [])}]
    return []

def motivos_conteudo(body):
    n = normalizar_chave(body)
    reasons = []
    for match in re.finditer('anex\\w*|manual\\w*|monografia\\w*|tabela\\w*|leiaute\\w*|plano\\w*', n):
        ctx = n[max(0, match.start() - 180):match.end() + 240]
        if re.search('disponibil|sitio|portal|endereco eletronico|publicad\\w* no boletim|nao transcrit|nao reproduz|constam no|consta no', ctx):
            reasons.append({'motivo': 'remissão externa exige contexto', 'trecho': ctx})
    for pat in ['nao (?:transcrit\\w*|reproduzid\\w*)', 'anex\\w* const\\w* (?:no|do) (?:dodf|diario|boletim)', 'omitid\\w* por impossibilidade', 'publicad\\w* na integra (?:no|em)']:
        m = re.search(pat, n)
        if m:
            reasons.append({'motivo': 'aviso literal exige contexto', 'trecho': n[max(0, m.start() - 180):m.end() + 240]})
    own = re.search('anex\\w* (?:a est[ae]|dest[ae]|que (?:integra|acompanha))|(?:na forma|nos termos|conforme) d[oa] anex\\w*|aprov\\w*.{0,100}anex\\w*', n)
    headings = list(re.finditer('(?im)^\\s*(?:#{1,6}\\s*)?(?:\\*\\*)?anex(?:o|os)\\b[^\\n]{0,160}$', body))
    if own and (not headings):
        reasons.append({'motivo': 'remissão potencialmente própria sem título de anexo', 'trecho': n[max(0, own.start() - 150):own.end() + 200]})
    if headings and len(body[headings[-1].end():].strip()) < 80:
        reasons.append({'motivo': 'último título de anexo sem conteúdo substancial'})
    text = html.unescape(re.sub('<[^>]+>', ' ', body))
    start = re.search('\\bArt(?:igo)?\\.?\\s*\\*{0,2}\\s*1[ºo°.]?\\b|\\bI\\s*[-–.]', text, re.I)
    if start:
        window = text[start.start():start.start() + 2500]
        end = re.search('\\bArt(?:igo)?\\.?\\s*\\*{0,2}\\s*2[ºo°.]?\\b', window, re.I)
        if end:
            window = window[:end.start()]
        approval = re.search('\\baprova(?:r|m|d[oa]s?)?\\b[\\s\\S]{0,190}?\\b(documento|manual|plano|programa|regulamento|regimento|estatuto|projeto|quadro|tabela|c[oó]digo|conv[eê]nio|acordo|termo)\\b', window, re.I)
        if approval:
            reasons.append({'motivo': 'objeto aprovado no dispositivo inicial exige contexto', 'trecho': window[:2000]})
    decoded = body
    for _ in range(3):
        decoded = html.unescape(decoded)
    placeholder = re.search('(?im)^\\s*(?:#{1,6}\\s*)?(?:(?:<|\\[){1,3}\\s*(?:anex[oa]s?|tabela|quadro|modelo|planilha)\\b[^\\n]{0,180}(?:>|\\])|(?:anexo|tabela|quadro|modelo|planilha)[^\\n]{0,100}(?:omitid|n[aã]o\\s+(?:transcrit|reproduz)|vide\\s+(?:publica|original)))', decoded)
    if placeholder:
        reasons.append({'motivo': 'placeholder de suplemento exige contexto', 'trecho': placeholder[0]})
    return reasons
