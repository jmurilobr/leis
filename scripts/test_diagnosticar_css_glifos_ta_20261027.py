"""Escopo municipal, herança, overrides e condições sem inferência jurídica."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from diagnosticar_css_glifos_ta_20261027 import analisar

def run(inner,css='',ancestor=''):
 source='<html><head><style>'+css+'</style></head><body><section '+ancestor+'>'+inner+'</section></body></html>'
 return analisar(source,source.encode(),'controle','controle','controle','teste')
def active(r):return [x for x in r['eventos_texto_efetivo_DOM'] if x['escopo'] in {'ativo','epigrafe'}]

class CSSMunicipal(unittest.TestCase):
 def test_historico_nao_e_ativo(self):
  r=run('<div class="dptt desativado" id="old" style="font-family:Symbol">F</div><div class="dptt" id="new">Texto</div>')
  self.assertFalse(active(r));self.assertEqual(r['eventos_texto_efetivo_DOM'][0]['escopo'],'historico_desativado')
 def test_ocultacao_ancestral(self):self.assertTrue(active(run('<div class="dptt" id="new">Texto</div>',ancestor='style="display:none"'))[0]['ocultacao_css'])
 def test_override_fonte_do_filho(self):self.assertFalse(active(run('<div class="dptt" id="new" style="font-family:Symbol"><span style="font-family:Arial">F</span></div>')))
 def test_regra_inutilizada(self):
  r=run('<div class="dptt" id="new">Texto</div>','.ausente{font-family:Wingdings}')
  self.assertFalse(active(r));self.assertTrue(r['regras_perigosas_sem_match_normativo'])
 def test_cascata_important(self):self.assertTrue(active(run('<div class="dptt" id="new" style="font-family:Arial">F</div>','.dptt{font-family:Symbol!important}'))[0]['fonte_especial_aplicada_css'])
 def test_revogado_literal_e_tachado_distintos(self):
  r=run('<div class="dptt revogado" id="new">Art. 1º (Revogado)</div>')
  self.assertTrue(r['dispositivos_ativos_classe_revogado'][0]['rotulo_literal_revogado']);self.assertFalse(active(r))
  r=run('<div class="dptt" id="new"><del>redação anterior</del>Texto</div>');self.assertTrue(active(r)[0]['tags_s_del_strike'])
 def test_condicional_nao_e_computada(self):
  r=run('<div class="dptt" id="new">F</div>','@media print{.dptt{font-family:Symbol}}')
  self.assertFalse(active(r));self.assertTrue(r['regras_condicionais_com_match'])
 def test_epigrafe_incluida_menu_excluido(self):
  r=run('<nav style="font-family:Symbol">F</nav><h1 class="page-header" style="font-family:Symbol">Título</h1><div class="dptt" id="new">Texto</div>')
  self.assertEqual([x['escopo'] for x in active(r)],['epigrafe'])
 def test_visibility_filho_pode_restaurar(self):self.assertFalse(active(run('<div class="dptt" id="new" style="visibility:hidden"><span style="visibility:visible">Texto</span></div>')))
 def test_display_filho_nao_restaura_ancestral(self):self.assertTrue(active(run('<div class="dptt" id="new" style="display:none"><span style="display:block">Texto</span></div>'))[0]['ocultacao_css'])

if __name__=='__main__':unittest.main()
