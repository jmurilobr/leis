"""Piloto CONFAZ: sem rede, sem Git de escrita e sem edição de canônicos."""
from pathlib import Path
import json
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from confaz_auditar_piloto_privado_v3_20261027 import campo,representar,historico_identificado,auditar_css,texto_visivel_html,ROOT
from confaz_confrontar_head_privado_v2_20261027 import key,label_key,metadata_key,MarkdownIt
from confaz_preparar_candidatos_privados_20261027 import dia_captura


class PilotoCONFAZ(unittest.TestCase):
    def test_campo_unico_preserva_utf8_e_limites(self):
        field='<div id="parent-fieldname-text"><p>Cláusula 1ª: 0,5% – R$ 2,00.</p><div>Fecho.</div></div>'
        self.assertEqual(campo('<div>navegação</div>'+field+'<div>rodapé</div>'),field)
        with self.assertRaises(ValueError):campo(field+field)

    def test_seis_casos_reais_sem_alteracao_de_texto_e_atributos(self):
        base=ROOT/'reguladores/_fonte/auditorias/confaz-piloto-qa-v3-20261027'
        for number in range(121,127):
            source=(base/str(number)/'campo-original.html').read_text();native=representar(source)
            self.assertEqual(texto_visivel_html(source),texto_visivel_html(native))
            self.assertFalse(historico_identificado(source))
            self.assertIn('Cláusula',texto_visivel_html(native))

    def test_historico_real35_passa_texto_mas_nao_pode_ser_liberado(self):
        base=ROOT/'reguladores/_fonte/auditorias'
        field=(base/'confaz-controle-historico35-qa-v3-20261027/35/campo-original.html').read_text()
        self.assertEqual(texto_visivel_html(field),texto_visivel_html(representar(field)))
        history=historico_identificado(field)
        self.assertGreaterEqual(len(history),8)
        r=json.loads((base/'confaz-controle-historico35-qa-v3-20261027/35/controle.json').read_text())
        self.assertEqual(r['estado'],'retido');self.assertIn('Histórico',r['motivo'])

    def test_tachados_ativos_e_pre_ficam_retidos(self):
        for extra in ['<s>antigo</s>','<script>x()</script>','<p hidden>antigo</p>','<pre>A\n\nB</pre>']:
            with self.subTest(extra=extra),self.assertRaises(ValueError):representar('<div id="parent-fieldname-text">'+extra+'</div>')

    def test_css_aplicavel_difere_de_menu_alheio(self):
        page='<html><head><style>.menu{display:none}.antigo{text-decoration:line-through}</style></head><body><div class="menu">Menu</div><div id="parent-fieldname-text"><p class="antigo">Texto.</p></div></body></html>'
        r=auditar_css(page,'https://www.confaz.fazenda.gov.br/controle',{})
        self.assertEqual(len(r['riscos_aplicaveis']),1)
        self.assertIn('.antigo',r['riscos_aplicaveis'][0]['regra']['seletor'])

    def test_identidade_alias_nao_e_ato_cotepe_com_mesmo_numero(self):
        engine=MarkdownIt('commonmark',{'html':True})
        m=dict(tipo='Convênio ICMS',numero='121',data='2026-10-13',orgao='CONFAZ')
        self.assertEqual(metadata_key(m),('Convênio ICMS',121,2026))
        self.assertEqual(label_key('CONVÊNIO ICMS 121/26','2026-10-13'),('Convênio ICMS',121,2026))
        self.assertIsNone(metadata_key(dict(tipo='Ato Normativo',numero='121',data='2026-10-13',orgao='CONFAZ')))
        self.assertIsNone(key(m,'# Metadados\n\nATO COTEPE Nº 121, DE 13 DE OUTUBRO DE 2026\n\nCONFAZ',engine))
        source=(ROOT/'reguladores/_fonte/auditorias/confaz-piloto-qa-v3-20261027/121/campo-original.html').read_text()
        self.assertEqual(key(m,'# Metadados\n\n'+representar(source),engine),('Convênio ICMS',121,2026))

    def test_publicacao_sem_classe_css_e_condicao_ratificacao_preservadas(self):
        base=ROOT/'reguladores/_fonte/auditorias/confaz-piloto-qa-v3-20261027'
        for n in range(121,127):
            r=json.loads((base/str(n)/'controle.json').read_text())
            self.assertTrue(any('Publicado no DOU' in p for p in r['notas_publicacao_ratificacao_literais']))
            self.assertTrue(any('ratificação nacional' in p for p in r['condicoes_efeitos_literais']))
        candidates=json.loads((ROOT/'reguladores/_fonte/auditorias/confaz-piloto-candidatos-v2-20261027/mapa-candidatos.json').read_text())
        self.assertEqual(candidates['candidatos'],6)
        for r in candidates['resultados']:
            self.assertIsNone(r['metadata']['revogada'])
            self.assertNotIn('data_vigencia',r['metadata'])

    def test_data_da_captura_nao_e_data_de_materializacao(self):
        day,_=dia_captura(dict(capturado_em_cliente='2026-10-28T01:00:00+00:00'),'2026-10-27')
        self.assertEqual(day,'2026-10-27')
        with self.assertRaises(ValueError):dia_captura(dict(capturado_em_cliente='2026-10-27T12:00:00'),'2026-10-27')


if __name__=='__main__':unittest.main()
