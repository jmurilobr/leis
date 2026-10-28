from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from perfil_ta_tachados_preservados_20261027 import converter,comparar,R
from converter_organica_fortaleza import converter as anterior

def source(text):return '<html><head></head><body><div class="cp"><div class="dptt" id="dptt1">'+text+'</div></div></body></html>'

class PerfilTachados(unittest.TestCase):
 def test_fecho_real_buritis(self):
  s=(R/'municipais/_indice/_recuperacao_20261027/css-glifos-ta4735-20261027/buritis8-1971-fonte.html').read_text();body,p=converter(s)
  self.assertIn('~~Sebastião Alves~~\n\n~~Secretário~~\n\nSecretário Substituto',body)
  self.assertNotIn('Nota editorial',body);self.assertTrue(p.prova_tachados_preservados['marcacao_tachado_por_caractere_confere'])
  self.assertEqual([r['texto'] for r in p.prova_tachados_preservados['markup_tachado_renderizado']],['Sebastião Alves','Secretário'])
 def test_texto_igual_sem_markup_nao_basta(self):
  s=source('<p><s>Secretário</s> Substituto</p>');r=comparar(s,'Secretário Substituto')
  self.assertTrue(r['igualdade_caracteres_nao_brancos']);self.assertFalse(r['marcacao_tachado_por_caractere_confere']);self.assertFalse(r['aprovado'])
 def test_tachado_em_ocorrencia_errada(self):self.assertFalse(comparar(source('<s>Nome</s> Nome'),'Nome ~~Nome~~')['aprovado'])
 def test_del_strike_css_inline_preservados(self):
  for mark in ['<del>1,5%</del>','<strike>1,5%</strike>','<span style="text-decoration:line-through">1,5%</span>']:
   with self.subTest(mark=mark):self.assertTrue(converter(source(mark+' novo'))[1].prova_tachados_preservados['aprovado'])
 def test_numero_tachado_nao_pode_sumir(self):self.assertFalse(comparar(source('<s>1,5%</s> novo'),'novo')['aprovado'])
 def test_atributo_contextual_nao_pode_sumir(self):
  r=comparar(source('<del datetime="2020-01-01" title="nota própria">Nome</del>'),'~~Nome~~');self.assertTrue(r['marcacao_tachado_por_caractere_confere']);self.assertFalse(r['atributos_contextuais_tachados_conferem']);self.assertFalse(r['aprovado'])
  with self.assertRaisesRegex(ValueError,'Atributos contextuais'):converter(source('<del datetime="2020-01-01">Nome</del>'))
 def test_regra_css_tachado_aplicada_retem(self):
  with self.assertRaisesRegex(ValueError,'regra CSS'):converter(source('<style>.x{text-decoration:line-through}</style><p class="x">Nome</p>'))
 def test_regra_css_sem_uso_nao_inventa_tachado(self):self.assertTrue(converter('<html><head><style>.semuso{text-decoration:line-through}</style></head><body><div class="dptt" id="one">Nome</div></body></html>')[1].prova_tachados_preservados['aprovado'])
 def test_condicional_so_no_historico_nao_retem_ativo(self):
  s='<html><head><style>@media print{.hist{font-family:Symbol}}</style></head><body><div class="dptt" id="one">Atual</div><div class="dptt desativado hist" id="old">Outro</div></body></html>';self.assertTrue(converter(s)[1].prova_tachados_preservados['aprovado'])
 def test_historico_desativado_continua_separado(self):
  s=source('Atual').replace('</body>','<div class="dptt desativado" id="old"><s>Outro</s></div></body>');body,p=converter(s);self.assertEqual(body,anterior(s)[0]);self.assertNotIn('Outro',body);self.assertEqual(p.prova_tachados_preservados['historicos_excluidos'],['old'])
 def test_compatibilidade_sem_tachado(self):
  s=source('<p>Art. 1º – Texto <strong>12,5%</strong>.</p><p>Fecho.</p>');self.assertEqual(converter(s)[0],anterior(s)[0])
 def test_tabela_sem_tachado_preserva_celulas(self):
  body,p=converter(source('<table><tr><td>0</td><td>3,5</td></tr></table>'));self.assertEqual(p.prova_tachados_preservados['prova_tabelas']['tabelas'],1)
 def test_tabela_tachada_permanece_retida(self):
  with self.assertRaises(ValueError):converter(source('<table><tr><td><s>0</s></td></tr></table>'))
 def test_ocultacao_e_fonte_especial_retem(self):
  for style in ['display:none','font-family:Symbol']:
   with self.subTest(style=style):
    with self.assertRaises(ValueError):converter(source('<span style="'+style+'">F</span>'))

if __name__=='__main__':unittest.main()
