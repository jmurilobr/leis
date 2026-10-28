"""Replay independente de pontuação e números em lotes federais congelados.

Não altera MDs, fontes ou manifestos de entrada. A comparação primária conserva
pontuação e contexto; a reconversão é apenas um controle adicional, não oráculo.
"""
import argparse
import concurrent.futures
import datetime
import difflib
import gzip
import html
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estados import pe_fidelidade_visivel as fidelidade
from preparar_lote_decretos_cache import fields
from html2md import convert

ROOT = Path(__file__).resolve().parent.parent

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def contexto_numerico(text):
    pattern = r'(?:US\$|R\$|[€£$])?\s*[+−–—-]?\s*\d+(?:[.,:/-]\d+)*(?:\s*[%‰])?'
    return [{'token': m[0].strip(), 'antes': text[max(0, m.start()-45):m.start()],
             'depois': text[m.end():m.end()+45]} for m in re.finditer(pattern, text)]


def diferencas(source, actual):
    matcher = difflib.SequenceMatcher(a=source, b=actual, autojunk=True)
    result = []
    for op, i, j, k, l in matcher.get_opcodes():
        if op == 'equal':
            continue
        result.append({'operacao': op, 'fonte': source[i:j], 'md': actual[k:l],
                       'contexto_fonte': source[max(0, i-60):min(len(source), j+60)],
                       'contexto_md': actual[max(0, k-60):min(len(actual), l+60)]})
        if len(result) == 20:
            break
    return result


def normalizar_marcador_administrativo(source, row):
    """Exclui apenas códigos administrativos vinculados à identidade própria.

    Conserva prefixos literais =/@ e o sufixo RET01+++. Códigos repetidos são
    aceitos somente como identificadores de retificação após um código inicial
    comprovado; nunca apaga pontuação nem palavras do dispositivo.
    """
    expected = row.get('epigrafe', {})
    pattern = re.compile(r'###DEC-(\d+)-(0|[A-Z])-000-(\d{2})-(\d{2})-(\d{4})@@@')
    replacements = []
    for paragraph in re.finditer(r'<p\b[^>]*>.*?</p>', source, re.I | re.S):
        text = fidelidade.texto_visivel_html(paragraph[0])
        marker = pattern.search(text)
        if not marker:
            continue
        number, suffix, day, month, year = marker.groups()
        number = str(int(number)) + ('-'+suffix.lower() if suffix != '0' else '')
        date = year+'-'+month+'-'+day
        if number != expected.get('numero', '').lower() or date != expected.get('data'):
            return source, None
        if ':decreto:'+date+';'+number != row['urn'][row['urn'].index(':decreto:'):]:
            return source, None
        prefix = text[:marker.start()]
        remainder = text[marker.end():]
        before = fidelidade.texto_visivel_html(source[:paragraph.start()])
        initial = not before and prefix in {'', '=', '-'} and remainder in {'', '@', '.'}
        correction = bool(replacements) and not prefix and bool(re.fullmatch(r'RET\d+\+{3}', remainder))
        if not (initial or correction):
            return source, None
        replacements.append({'inicio': paragraph.start(), 'fim': paragraph.end(),
                             'paragrafo_html': paragraph[0], 'marcador': marker[0],
                             'prefixo_literal_preservado': prefix,
                             'sufixo_literal_preservado': remainder,
                             'numero': number, 'data': date,
                             'sha256_paragrafo_html': sha(paragraph[0].encode())})
    if not replacements:
        return source, None
    cleaned = source
    for record in reversed(replacements):
        cleaned = cleaned[:record['inicio']] + '<p>'+html.escape(record['prefixo_literal_preservado']+record['sufixo_literal_preservado'])+'</p>' + cleaned[record['fim']:]
    return cleaned, {'natureza': 'Marcador administrativo de cadastro com identidade comprovada.',
                     'prova': 'Código inicial fora do dispositivo e códigos de retificação da mesma identidade. Número, complemento e data coincidem com a epígrafe e a URN. Todos os demais caracteres permanecem intactos.',
                     'paragrafos': replacements}


def conferir(row):
    path = row['path']
    sourcepath = row.get('fonte_html_cache', path.replace('federal/decretos/', 'federal/_fonte/decretos/').replace('.md', '.html.gz'))
    md_raw = (ROOT/path).read_bytes()
    html_raw = gzip.decompress((ROOT/sourcepath).read_bytes())
    assert sha(md_raw) == row['sha256'], 'MD diverge do lote congelado: '+path
    assert sha(html_raw) == row['sha256_fonte_html'], 'Fonte diverge do lote congelado: '+path
    meta, _, body = fields(md_raw.decode())
    body = body.lstrip()
    title, separator, body = body.partition('\n')
    assert separator and title == '# '+meta['titulo'], 'Título editorial inicial inesperado: '+path
    source = html_raw.decode('utf8')
    normalized_source, administrative_marker = normalizar_marcador_administrativo(source, row)
    proof = fidelidade.comparar_fidelidade(normalized_source, convert(source), body)
    src = proof['visivel_fonte']
    actual = proof['visivel_md_apos_heading_comprovado']
    numeric_source = fidelidade.assinatura_numerica(src)
    numeric_md = fidelidade.assinatura_numerica(actual)
    contexts_source = contexto_numerico(src)
    contexts_md = contexto_numerico(actual)
    equal = proof['texto_visivel_md_igual_fonte_apos_formato_heading_comprovado']
    record = {'path': path, 'urn': row['urn'], 'fonte': row['fonte'],
              'fonte_html_cache': sourcepath, 'sha256_md': sha(md_raw),
              'sha256_fonte_html': sha(html_raw),
              'texto_visivel_com_pontuacao_igual': equal,
              'assinatura_numerica_igual': numeric_source == numeric_md,
              'contextos_numericos_iguais': contexts_source == contexts_md,
              'reconversao_visivel_igual_md': proof['texto_visivel_md_igual_reconversao'],
              'sha256_visivel_fonte': sha(src.encode()),
              'sha256_visivel_md': sha(actual.encode()),
              'sha256_assinatura_numerica_fonte': sha(json.dumps(numeric_source, ensure_ascii=False).encode()),
              'sha256_assinatura_numerica_md': sha(json.dumps(numeric_md, ensure_ascii=False).encode()),
              'tokens_numericos': len(numeric_source),
              'normalizacoes_apresentacao': proof['normalizacoes_de_apresentacao'],
              'marcador_administrativo_excluido': administrative_marker}
    receipt = {**record, 'visivel_fonte': src, 'visivel_md': actual}
    if not equal or numeric_source != numeric_md or contexts_source != contexts_md:
        record['diferencas'] = diferencas(src, actual)
        record['contextos_numericos_fonte'] = contexts_source
        record['contextos_numericos_md'] = contexts_md
        receipt.update(record)
        receipt.update(fonte_html_utf8=source, md_utf8=md_raw.decode())
    return record, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifestos', nargs='+', required=True)
    parser.add_argument('--nome', required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9_]+', args.nome)
    output = ROOT/'federal'/('_auditoria_pontuacao_'+args.nome+'.json')
    receipt = ROOT/'federal'/('_receipts_pontuacao_'+args.nome+'.jsonl.gz')
    assert not output.exists() and not receipt.exists()
    rows = []; manifests = []; seen = set()
    for item in args.manifestos:
        raw = (ROOT/item).read_bytes(); document = json.loads(raw)
        manifests.append({'path': item, 'sha256': sha(raw)})
        for row in document['publicaveis']:
            assert row['path'] not in seen, row['path']
            seen.add(row['path']); rows.append(row)
    helperpath = Path(inspect.getfile(fidelidade))
    scripts = [Path(__file__).resolve(), helperpath.resolve()]
    result = {'criado_em': datetime.datetime.now().isoformat(), 'manifestos': manifests,
              'metodo': 'HTML primário contra texto visível do Markdown, preservando caixa, acentos, pontuação, decimais, separadores, sinais, moeda, percentuais, operadores e asteriscos literais. Apenas whitespace, BOM e markup de apresentação conhecido são normalizados. Títulos editoriais de html2md são normalizados somente com prova de adjacência literal na fonte. Marcadores administrativos ###DEC são excluídos somente com identidade e posição comprovadas, preservando prefixos e sufixos literais e arquivando cada parágrafo.',
              'codigos': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p.read_bytes())} for p in scripts],
              'auditados': [], 'divergencias_para_revisao': [], 'erros': []}
    with gzip.open(receipt, 'wt', encoding='utf8') as stream:
        stream.write(json.dumps({'codigo_exato': [{'path': str(p.relative_to(ROOT)), 'utf8': p.read_text(), 'sha256': sha(p.read_bytes())} for p in scripts]}, ensure_ascii=False)+'\n')
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            futures = {pool.submit(conferir, row): row for row in rows}
            for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
                row = futures[future]
                try:
                    record, proof = future.result()
                    if all(record[k] for k in ['texto_visivel_com_pontuacao_igual', 'assinatura_numerica_igual', 'contextos_numericos_iguais']):
                        result['auditados'].append(record)
                    else:
                        result['divergencias_para_revisao'].append(record)
                    stream.write(json.dumps(proof, ensure_ascii=False)+'\n')
                except Exception as error:
                    result['erros'].append({'path': row['path'], 'erro': str(error)})
                if count % 100 == 0 or count == len(rows):
                    print('REPLAY', count, '/', len(rows), 'divergências', len(result['divergencias_para_revisao']), 'erros', len(result['erros']), flush=True)
    result['resumo'] = {'candidatos': len(rows), 'sem_divergencia': len(result['auditados']),
                        'divergencias_para_revisao': len(result['divergencias_para_revisao']), 'erros': len(result['erros'])}
    result['receipts'] = {'path': str(receipt.relative_to(ROOT)), 'sha256': sha(receipt.read_bytes())}
    result['limite'] = 'Não substitui validação de identidade, anexos, figuras ou vigência. Divergências conservadoras exigem revisão contextual; ausência de alerta não é declaração de completude jurídica.'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print('FIM', output, result['resumo'], flush=True)


if __name__ == '__main__':
    main()
