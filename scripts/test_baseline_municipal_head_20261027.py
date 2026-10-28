"""Regressões de cabeçalho integral e reserva; não executa Git de escrita."""
import hashlib
import contextlib
import gzip
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import congelar_baseline_municipal_head_20261027 as baseline
import comparar_baseline_municipal_head_20261027 as compare


def documento(url,extra=''):
    return ('---\ntitulo: "Lei nº 1"\ntipo: "Lei Ordinária"\nnumero: "1"\ndata: "2020-01-01"\n'+extra+
            'fonte: '+json.dumps(url)+'\n---\n# Lei nº 1\n\nArt. 1º Texto.\n').encode()


class BaselineHEAD(unittest.TestCase):
    def test_metadado_apos_mais_de_16k_nao_e_truncado(self):
        raw=documento('https://oficial.leg.br/norma/1','observacao: '+json.dumps('x'*40000)+'\n')
        r=baseline.registro('municipais/SP/teste/leis/2020/lei1.md','a'*40,raw,'HEAD')
        self.assertEqual(r['metadados']['fonte'],'https://oficial.leg.br/norma/1')
        self.assertIn(['url','https://oficial.leg.br/norma/1'],[list(k) for k in r['chaves']])
        self.assertEqual(r['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertGreater(len(r['cabecalho_integral']),40000)

    def test_registro_recebe_blob_em_vez_de_substituir_por_arquivo_local(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'privado.md';p.write_bytes(documento('https://privado.leg.br/norma/9'))
            raw=documento('https://publicado.leg.br/norma/1')
            r=baseline.registro('municipais/SP/teste/leis/2020/lei1.md','b'*40,raw,'HEAD')
            self.assertEqual(r['metadados']['fonte'],'https://publicado.leg.br/norma/1')
            self.assertNotEqual(r['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())

    def test_reserva_sha_e_conflito_com_head(self):
        with tempfile.TemporaryDirectory() as d, patch.object(baseline,'ROOT',Path(d)):
            root=Path(d);name='municipais/SP/teste/leis/2020/lei1.md';p=root/name;p.parent.mkdir(parents=True);p.write_bytes(documento('https://oficial.leg.br/norma/1'))
            lista=root/'lista.txt';lista.write_text(name+'\n')
            records=[dict(arquivo=x,sha256=baseline.sha((root/x).read_bytes()),bytes=(root/x).stat().st_size) for x in [name,'lista.txt']]
            receipt=root/'recibo.json';receipt.write_text(json.dumps(dict(arquivos=records,normas=1,lista_normas='lista.txt')))
            digest=baseline.sha(receipt.read_bytes())
            with self.assertRaisesRegex(ValueError,'SHA do recibo'):baseline.reservas(receipt,'0'*64,{})
            rows,proof=baseline.reservas(receipt,digest,{})
            self.assertEqual(len(rows),1);self.assertEqual(proof['adicionadas'],1)
            with self.assertRaisesRegex(ValueError,'diverge do blob HEAD'):
                baseline.reservas(receipt,digest,{name:dict(sha256='0'*64)})

    def test_comparador_colide_com_blob_head_apesar_de_working_tree_diferente(self):
        with tempfile.TemporaryDirectory() as d:
            previous=Path.cwd();os.chdir(d)
            try:
                old='municipais/SP/teste/leis/2020/lei1.md';new='municipais/SP/teste/leis/2020/lei2.md'
                Path(old).parent.mkdir(parents=True)
                published=documento('https://oficial.leg.br/norma/1')
                Path(old).write_bytes(documento('https://privado.leg.br/norma/9'))
                Path(new).write_bytes(published)
                row=baseline.registro(old,'a'*40,published,'HEAD')
                with gzip.open('metadados.gz','wt') as f:f.write(json.dumps(row)+'\n')
                p=Path('metadados.gz')
                Path('snapshot.json').write_text(json.dumps(dict(commit='b'*40,metadados=str(p),total=1,
                    arquivos=[dict(arquivo=str(p),sha256=compare.sha(p),bytes=p.stat().st_size)])))
                Path('candidatos.txt').write_text(new+'\n')
                with patch.object(sys,'argv',['comparar','--baseline','snapshot.json','--lista','candidatos.txt','--saida','controle.json']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(compare.main(),1)
                result=json.loads(Path('controle.json').read_text())
                self.assertTrue(result['colisoes'])
                self.assertEqual(result['colisoes'][0]['existentes'][0]['oid'],'a'*40)
                self.assertEqual(result['colisoes'][0]['existentes'][0]['sha256'],hashlib.sha256(published).hexdigest())
            finally:os.chdir(previous)


if __name__=='__main__':unittest.main()
