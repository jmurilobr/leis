"""Regressões das provas exigidas para publicar um documento do cache DOU."""
import datetime as dt
import gzip
import hashlib
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import auditar_cache_dou as audit


class CacheDOU(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        p = patch.object(audit, 'RAIZ', self.root)
        p.start()
        self.addCleanup(p.stop)
        self.path = self.root / 'reguladores/ans/portarias/2026/portaria-1-123456789.md'
        self.title = 'PORTARIA Nº 1, DE 1 DE OUTUBRO DE 2026'

    def fixture(self, extra='', publicacao='02/10/2026', corromper=False,
                orgao_meta='ANS', orgao_html='ANS'):
        fragment = (f'<div class="texto-dou"><p class="identifica">{self.title}</p>'
                    '<p>Art. 1º Fica instituído o procedimento descrito nesta norma.</p>'
                    '<p>Art. 2º Esta portaria entra em vigor na data de sua publicação.</p>' + extra + '</div>')
        source = (f'<span class="publicado-dou-data">{publicacao}</span>'
                  f'<span class="orgao-dou-data">{orgao_html}</span><span class="edicao-dou-data">123</span>' +
                  fragment + '<div>rodapé</div>').encode()
        sha = hashlib.sha256(source).hexdigest()
        cache = self.root / ('reguladores/_fonte/ans/2026/' + self.path.stem + '-' + sha + '.html.gz')
        cache.parent.mkdir(parents=True)
        cache.write_bytes(gzip.compress(source + (b' ' if corromper else b'')))
        meta = {'titulo': self.title, 'tipo': 'Portaria', 'numero': '1', 'data': '2026-10-01',
                'orgao': orgao_meta, 'revogada': None, 'versao_texto': 'publicação original',
                'data_publicacao': '2026-10-02', 'edicao': '123',
                'fonte': 'https://www.in.gov.br/web/dou/-/portaria-1-123456789',
                'sha256_html_fonte': sha, 'baixado_em': '2026-10-20'}
        self.path.parent.mkdir(parents=True)
        self.path.write_text('---\n' + ''.join(k + ': ' + json.dumps(v, ensure_ascii=False) + '\n' for k,v in meta.items()) +
                             '---\n# ' + self.title + '\n\n' + audit.convert(fragment))

    def conferir(self):
        return audit.conferir(self.path, set(), set(), dt.date(2026, 10, 20))

    def layout_legado(self, titulo=None, repetido=False, intervalo=''):
        self.fixture()
        cache = next((self.root / 'reguladores/_fonte/ans/2026').glob('*.gz'))
        source = gzip.decompress(cache.read_bytes()).decode()
        old_sha = hashlib.sha256(source.encode()).hexdigest()
        source = source.replace(f'<p class="identifica">{self.title}</p>', '')
        heading = '<h3 class="titulo-dou"><span>' + (titulo or self.title) + '</span></h3>'
        source = source.replace('<div class="texto-dou">', heading * (2 if repetido else 1) + intervalo + '<div class="texto-dou">')
        fragmento = re.search(r'<div class="texto-dou">.*?</div>', source, re.S)[0]
        new_sha = hashlib.sha256(source.encode()).hexdigest()
        cache.unlink()
        cache.with_name(cache.name.replace(old_sha, new_sha)).write_bytes(gzip.compress(source.encode()))
        cab = self.path.read_text().split('\n---\n', 1)[0].replace(old_sha, new_sha)
        self.path.write_text(cab + '\n---\n# ' + self.title + '\n\n' + audit.convert(fragmento))

    def test_layout_legado_epigrafe_propria_adjacente(self):
        self.layout_legado(intervalo='\n\n')
        antes = self.path.read_bytes()
        registro, _ = self.conferir()
        self.assertEqual(registro['epigrafe_html'], self.title)
        self.assertIn('h3.titulo-dou', registro['origem_epigrafe'])
        self.assertEqual(self.path.read_bytes(), antes)

    def test_layout_legado_titulo_divergente_retem(self):
        self.layout_legado(titulo='PORTARIA Nº 2, DE 1 DE OUTUBRO DE 2026')
        with self.assertRaisesRegex(ValueError, 'epígrafe própria diverge'):
            self.conferir()

    def test_layout_legado_dois_titulos_externos_retem(self):
        self.layout_legado(repetido=True)
        with self.assertRaisesRegex(ValueError, 'múltiplas/ausentes'):
            self.conferir()

    def test_layout_legado_titulo_nao_adjacente_retem(self):
        self.layout_legado(intervalo='<p>Outro documento</p>')
        with self.assertRaisesRegex(ValueError, 'múltiplas/ausentes'):
            self.conferir()

    def test_layout_legado_sem_epigrafe_na_fonte_retem(self):
        self.layout_legado()
        source = '<div class="texto-dou"><p>Corpo sem título</p></div>'
        with self.assertRaisesRegex(ValueError, 'múltiplas/ausentes'):
            audit.epigrafe_do_ato(source, source, 0)

    def test_epigrafe_interna_divergente_nao_cede_ao_titulo_externo(self):
        self.fixture()
        fragmento = '<div class="texto-dou"><p class="identifica">PORTARIA Nº 2</p></div>'
        prefixo = f'<h3 class="titulo-dou">{self.title}</h3>'
        titulo, origem = audit.epigrafe_do_ato(prefixo + fragmento, fragmento, len(prefixo))
        self.assertEqual(titulo, 'PORTARIA Nº 2')
        self.assertIn('p.identifica', origem)

    def test_hierarquia_espacos_preserva_valores_originais(self):
        self.fixture(orgao_meta='ANS/Diretoria Normativa', orgao_html='ANS / Diretoria Normativa')
        antes = self.path.read_bytes()
        registro, _ = self.conferir()
        self.assertEqual(registro['orgao_html'], 'ANS / Diretoria Normativa')
        self.assertEqual(registro['orgao_metadados'], 'ANS/Diretoria Normativa')
        self.assertEqual(self.path.read_bytes(), antes)

    def test_hierarquia_departamento_diferente_retem(self):
        self.fixture(orgao_meta='ANS/Diretoria Normativa', orgao_html='ANS / Diretoria Fiscal')
        with self.assertRaisesRegex(ValueError, 'órgão diverge'):
            self.conferir()

    def test_hierarquia_ordem_diferente_retem(self):
        self.fixture(orgao_meta='ANS/Diretoria Normativa', orgao_html='Diretoria Normativa / ANS')
        with self.assertRaisesRegex(ValueError, 'órgão diverge'):
            self.conferir()

    def test_hierarquia_nivel_vazio_retem(self):
        self.fixture(orgao_meta='ANS//Diretoria Normativa', orgao_html='ANS / / Diretoria Normativa')
        with self.assertRaisesRegex(ValueError, 'órgão diverge'):
            self.conferir()

    def usar_nativo(self, modo='html-nativo-texto-dou-v1'):
        fonte = gzip.decompress(next((self.root / 'reguladores/_fonte/ans/2026').glob('*.gz')).read_bytes()).decode()
        fragmento = re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)', fonte, re.S)[0]
        cab, corpo = self.path.read_text().split('\n---\n', 1)
        if modo == 'html-nativo-texto-dou-v1':
            corpo = '# ' + self.title + '\n\n' + audit.representar_fragmento(fragmento, modo=modo)
        self.path.write_text(cab + '\nrepresentacao_corpo: ' + json.dumps(modo) + '\n---\n' + corpo)

    def test_html_nativo_explicitamente_provado_contra_fonte(self):
        self.fixture('<p><em>Clavibacter</em>: -100,50; 0,5%; R$ 2,00.</p>')
        self.usar_nativo()
        _, meta = self.conferir()
        self.assertEqual(meta['representacao_corpo'], 'html-nativo-texto-dou-v1')

    def test_html_nativo_nao_aceita_alterar_decimal(self):
        self.fixture('<p>Valor de referência: 0,5%.</p>')
        self.usar_nativo()
        self.path.write_text(self.path.read_text().replace('0,5%', '05%'))
        with self.assertRaisesRegex(ValueError, 'corpo diverge'):
            self.conferir()

    def test_modo_desconhecido_nao_recai_no_conversor_legado(self):
        self.fixture()
        self.usar_nativo('desconhecido')
        with self.assertRaisesRegex(ValueError, 'desconhecido'):
            self.conferir()

    def test_texto_integral_e_publicacao_confirmados(self):
        self.fixture()
        registro, _ = self.conferir()
        self.assertEqual(registro['data'], '2026-10-01')

    def test_dois_atos_na_pagina_exigem_separacao_validada(self):
        self.fixture('<p class="identifica">PORTARIA Nº 2, DE 1 DE OUTUBRO DE 2026</p>')
        with self.assertRaisesRegex(ValueError, 'múltiplas'):
            self.conferir()

    def test_hash_da_fonte_corrompido_e_rejeitado(self):
        self.fixture(corromper=True)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.conferir()

    def test_publicacao_nao_pode_ser_inferida_do_markdown(self):
        self.fixture(publicacao='03/10/2026')
        with self.assertRaisesRegex(ValueError, 'publicação diverge'):
            self.conferir()

    def test_reextracao_truncada_nao_prova_integralidade(self):
        self.fixture('<div><p>ANEXO I</p></div><div><p>ANEXO II: valor 0</p></div>')
        fonte = gzip.decompress(next((self.root / 'reguladores/_fonte/ans/2026').glob('*.gz')).read_bytes()).decode()
        truncado = re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)', fonte, re.S)[0]
        cab = self.path.read_text().split('\n---\n', 1)[0]
        self.path.write_text(cab + '\n---\n# ' + self.title + '\n\n' + audit.convert(truncado))
        with self.assertRaisesRegex(ValueError, 'não fechado'):
            self.conferir()


if __name__ == '__main__':
    unittest.main()
