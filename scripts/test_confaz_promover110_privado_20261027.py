"""Testes do runner privado CONFAZ; nunca executam --apply real."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from confaz_promover110_privado_20261027 import BASE, CANDIDATES, QA, sha, verify_manifest, validate_candidate, create_exclusive


class PromoverCONFAZ(unittest.TestCase):
    def test_gravacao_exclusiva_nao_sobrescreve(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, target = base / 'pronto', base / 'norma'
            source.write_bytes(b'integral')
            create_exclusive(source, target)
            self.assertFalse(source.exists())
            source2 = base / 'outro'
            source2.write_bytes(b'diferente')
            with self.assertRaises(FileExistsError):
                create_exclusive(source2, target)
            self.assertEqual(target.read_bytes(), b'integral')

    def test_symlink_ja_existente_nao_e_seguido(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / 'pronto'
            source.write_bytes(b'integral')
            target = base / 'norma'
            target.symlink_to(base / 'ausente')
            with self.assertRaises(FileExistsError):
                create_exclusive(source, target)
            self.assertFalse((base / 'ausente').exists())

    def test_manifesto_detecta_artefato_alterado(self):
        with tempfile.TemporaryDirectory(dir=BASE) as tmp:
            base = Path(tmp)
            source = base / 'fonte'
            source.write_bytes(b'oficial')
            manifest = base / 'manifesto.json'
            manifest.write_text(json.dumps(dict(arquivos=[dict(arquivo=str(source.relative_to(ROOT)), sha256=sha(source.read_bytes()), bytes=7)])))
            expected = sha(manifest.read_bytes())
            verify_manifest(manifest, expected)
            source.write_bytes(b'alterado')
            with self.assertRaises(ValueError):
                verify_manifest(manifest, expected)

    def real(self):
        row = json.loads(CANDIDATES.read_text())['resultados'][0]
        control = json.loads((QA / str(row['numero']) / 'controle.json').read_text())
        return row, control

    def test_candidato_real_reproduz_campo_integral(self):
        row, control = self.real()
        raw, target, _ = validate_candidate(row, control)
        self.assertEqual(sha(raw), row['sha256_md'])
        self.assertEqual(target, row['path_canonico_proposto'])

    def test_tipo_cotepe_com_numero_igual_nao_vira_convenio(self):
        row, control = self.real()
        row = copy.deepcopy(row)
        with tempfile.TemporaryDirectory(dir=BASE) as tmp:
            base = Path(tmp)
            raw = (ROOT / row['candidato']).read_bytes().replace(b'tipo: "Conv\xc3\xaanio ICMS"', b'tipo: "Ato COTEPE"')
            candidate, packed = base / 'candidato', base / 'compactado'
            candidate.write_bytes(raw)
            packed.write_bytes(gzip.compress(raw, mtime=0))
            row.update(candidato=str(candidate.relative_to(ROOT)), candidato_gzip=str(packed.relative_to(ROOT)),
                       sha256_md=sha(raw), bytes_md=len(raw), sha256_gzip=sha(packed.read_bytes()))
            with self.assertRaisesRegex(ValueError, 'Identidade formal'):
                validate_candidate(row, control)


if __name__ == '__main__':
    unittest.main()
