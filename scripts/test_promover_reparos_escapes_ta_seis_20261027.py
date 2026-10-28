"""Atomicidade e preimagens do runner seis; sem --apply em canônicos reais."""
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/bin/qa-20261027/python')]
from promover_reparos_escapes_ta_seis_20261027 import BASE, FROZEN, FROZEN_SHA, MAP, sha, verify_manifest, validate_row, replace_with_backup


class PromoverSeis(unittest.TestCase):
    def fixture(self, base):
        target, prepared, backup = base / 'alvo.md', base / 'preparado.txt', base / 'backup.txt'
        target.write_bytes(b'preimagem integral')
        target.chmod(0o640)
        prepared.write_bytes(b'candidato integral')
        return target, prepared, backup

    def test_troca_atomica_com_backup_e_modo(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, prepared, backup = self.fixture(Path(tmp))
            replace_with_backup(target, prepared, backup, sha(target.read_bytes()), sha(prepared.read_bytes()))
            self.assertEqual(target.read_bytes(), b'candidato integral')
            self.assertEqual(backup.read_bytes(), b'preimagem integral')
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertFalse(prepared.exists())

    def test_preimagem_divergente_nao_e_tocada(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, prepared, backup = self.fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError, 'Preimagem/preparado'):
                replace_with_backup(target, prepared, backup, '0' * 64, sha(prepared.read_bytes()))
            self.assertEqual(target.read_bytes(), b'preimagem integral')
            self.assertFalse(backup.exists())
            self.assertTrue(prepared.exists())

    def test_backup_existente_nao_e_sobrescrito(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, prepared, backup = self.fixture(Path(tmp))
            backup.write_bytes(b'backup anterior')
            with self.assertRaises(FileExistsError):
                replace_with_backup(target, prepared, backup, sha(target.read_bytes()), sha(prepared.read_bytes()))
            self.assertEqual(target.read_bytes(), b'preimagem integral')
            self.assertEqual(backup.read_bytes(), b'backup anterior')

    def test_symlink_nao_e_substituido(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target, prepared, backup = self.fixture(base)
            link = base / 'link.md'
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                replace_with_backup(link, prepared, backup, sha(target.read_bytes()), sha(prepared.read_bytes()))
            self.assertEqual(target.read_bytes(), b'preimagem integral')

    def test_manifesto_rejeita_artefato_alterado(self):
        with tempfile.TemporaryDirectory(dir=BASE) as tmp:
            base = Path(tmp)
            source = base / 'fonte.txt'
            source.write_bytes(b'original')
            manifest = base / 'manifesto.json'
            manifest.write_text(json.dumps(dict(arquivos=[dict(arquivo=str(source.relative_to(ROOT)), sha256=sha(source.read_bytes()), bytes=8)])))
            expected = sha(manifest.read_bytes())
            verify_manifest(manifest, expected)
            source.write_bytes(b'alterado')
            with self.assertRaises(ValueError):
                verify_manifest(manifest, expected)

    def test_94_artefatos_e_seis_fontes_reais(self):
        self.assertEqual(len(verify_manifest(FROZEN, FROZEN_SHA)['arquivos']), 94)
        names = [r['nome'] for r in json.loads((ROOT / 'municipais/_indice/ibge-municipios.json').read_text())]
        rows = json.loads(MAP.read_text())['candidatos']
        self.assertEqual(len(rows), 6)
        for row in rows:
            current = sha((ROOT / row['path']).read_bytes())
            if current == row['sha256_preimagem']:
                _, _, proof = validate_row(row, names)
                self.assertTrue(proof['replay']['aprovado'])
            else:
                self.assertEqual(current, row['sha256_candidato'])
                with self.assertRaisesRegex(ValueError, 'Preimagem atual'):
                    validate_row(row, names)


if __name__ == '__main__':
    unittest.main()
