"""Adapta uma captura limitada do índice 2026 para os gates privados v3.

Não remove histórico, não escreve canônicos e não qualifica por igualdade
textual. Retificações e objetos sem identidade principal ficam separados.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from confaz_auditar_piloto_privado_v3_20261027 import campo


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captura', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    receipt = args.captura / 'manifesto-captura.json'
    source = json.loads(receipt.read_text())
    if source['incompletos'] or len(source['documentos']) != source['processados']:
        raise ValueError('Captura incompleta; conservar e revisar antes de adaptar')
    args.saida.mkdir(parents=True, exist_ok=False)
    pages, held = [], []
    counts = Counter((item['numero_indice'], item['ano']) for item in source['documentos']
                     if item['tipo_link_indice'] == 'principal')
    for item in source['documentos']:
        proof = item['fonte']
        row = dict(url=item['url'], numero=item['numero_indice'], ano=item['ano'], fonte=proof)
        try:
            raw = (ROOT / proof['arquivo']).read_bytes()
            if sha(raw) != proof['sha256'] or len(raw) != proof['bytes']:
                raise ValueError('Fonte mudou')
            if proof['status'] != 200 or item['css_pendentes']:
                raise ValueError('Fonte ou CSS incompletos')
            if item['tipo_link_indice'] != 'principal':
                raise ValueError('Retificação/republicação ou objeto separado exige modo próprio')
            if not isinstance(row['numero'], int) or row['ano'] != 2026:
                raise ValueError('Identidade principal do índice não confirmada')
            if counts[(row['numero'], row['ano'])] != 1:
                raise ValueError('Índice apresenta duas fontes principais para a mesma identidade')
            campo(raw.decode('utf-8'))
            pages.append(row)
        except Exception as error:
            held.append(dict(**row, estado='retido_preflight', motivo=str(error)))
    output = dict(paginas=pages, capturas=source['capturas'], incompletos=[],
                  captura_original=dict(path=str(receipt), sha256=sha(receipt.read_bytes())),
                  retidos_preflight=held, codigo_sha256=sha(Path(__file__).read_bytes()),
                  limite='Adaptador não libera normas. Todos os gates v3 e confronto formal HEAD permanecem obrigatórios; seis já publicados não são novas adições.')
    (args.saida / 'manifesto-captura.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(principais=len(pages), retidos_preflight=len(held))))


if __name__ == '__main__':
    main()
