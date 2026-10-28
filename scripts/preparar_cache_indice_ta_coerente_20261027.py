"""Valida e copia somente páginas de metadados de um snapshot TA coerente.

Não consulta a rede nem copia corpos. Conserva timestamps e provas originais;
a materialização usa um cache separado para evitar mistura de paginações.
"""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from congelar_indice_ta_coerente import paginar
ROOT = Path(__file__).resolve().parent.parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def carregar(path, host):
    manifest = json.loads(path.read_text())
    if not manifest['coerente'] or manifest['host'] != host or manifest['vinculo_sigi']['codigo_ibge'] is None:
        raise ValueError('Snapshot ou vínculo incompatível')
    index = {}
    for proof in manifest['paginas']:
        raw = (ROOT / proof['arquivo']).read_bytes()
        metadata = json.loads((ROOT / proof['metadata']).read_text())
        if proof['status'] != 200 or sha(raw) != proof['sha256'] or len(raw) != proof['bytes']:
            raise ValueError('Página do índice diverge da prova')
        if any(metadata[k] != proof[k] for k in ['url', 'url_final', 'status', 'sha256', 'capturado_em']):
            raise ValueError('Metadados da captura divergem da prova')
        if proof['url'] in index:
            raise ValueError('URL de página duplicada')
        index[proof['url']] = (json.loads(raw), proof)
    called = []
    def api(url):
        called.append(url)
        return index[url]
    rows, proofs, total = paginar(api, host)
    if len(called) != len(index) or total != manifest['total'] or len(rows) != manifest['ids_unicos']:
        raise ValueError('Índice não fecha com as páginas congeladas')
    return manifest, rows, proofs


def preparar(path, host, cache):
    manifest, rows, proofs = carregar(path, host)
    cache.mkdir(parents=True, exist_ok=True)
    for proof in proofs:
        raw = (ROOT / proof['arquivo']).read_bytes()
        target = cache / (sha(proof['url'].encode()) + '.json')
        metadata_path = target.with_suffix('.meta.json')
        info = json.loads((ROOT / proof['metadata']).read_text())
        info['cache_origem'] = proof['arquivo']
        info['metadata_origem'] = proof['metadata']
        if target.exists() or metadata_path.exists():
            if target.read_bytes() != raw or json.loads(metadata_path.read_text()) != info:
                raise ValueError('Cache separado já contém outra época do índice')
        else:
            with target.open('xb') as stream:
                stream.write(raw)
            with metadata_path.open('x') as stream:
                json.dump(info, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
    return manifest, rows
