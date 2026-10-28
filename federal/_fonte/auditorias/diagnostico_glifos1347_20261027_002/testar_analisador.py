from pathlib import Path
import ast,sys,hashlib,json,unittest,re
B=Path(__file__).resolve().parent;R=B.parents[3]
for p in ['scripts','scripts/bin/qa-20261027/python','scripts/bin/qa-html5-20261027/python']:sys.path.insert(0,str(R/p))
import tinycss2,cssselect2,html5lib
from identidade_decreto import extrair_epigrafe_decreto
source=(B/'diagnosticar.py').read_text();tree=ast.parse(source);names={'declarations','danger','text_of','node_signature','analyze'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'special','props'} for t in n.targets)];assert len(nodes)==7;sha=lambda x:hashlib.sha256(x).hexdigest();exec(compile(ast.Module(body=nodes,type_ignores=[]),'analisador_css_congelado','exec'))
def run(body,head='',admin=None,lote='748'):
 text='<html><head>'+head+'</head><body>'+body+'</body></html>';return analyze({'source':text,'source_raw':text.encode(),'path':'controle','lote':lote,'sha256_candidato':'controle','source_url':'controle','api_raw':'{}','normalizacao':admin})
def normative(r):return [x for x in r['eventos_texto_efetivo_DOM'] if x['escopo']=='normativo']
class CSS(unittest.TestCase):
 def test_symbol_inline(self):self.assertEqual(normative(run('<p style="font-family:Symbol">F</p>'))[0]['texto_literal'],'F')
 def test_wingdings_alias_sem_espaco(self):self.assertIsNotNone(normative(run('<p style="font-family:Wingdings2">F</p>'))[0]['fonte_especial_aplicada_css'])
 def test_regra_nao_aplicada(self):self.assertFalse(normative(run('<p>texto</p>','<style>.ausente{font-family:Webdings}</style>')))
 def test_fontface_nao_prova_uso(self):
  r=run('<p>texto</p>','<style>@font-face{font-family:Symbol;src:local(Symbol)}</style>');self.assertTrue(r['font_face_declarados_sem_provar_uso']);self.assertFalse(normative(r))
 def test_filho_sobrescreve_fonte(self):self.assertFalse(normative(run('<div style="font-family:Symbol"><span style="font-family:Arial">normal</span></div>')))
 def test_hidden_herdado_subarvore(self):self.assertTrue(normative(run('<div style="display:none"><span>oculto</span></div>'))[0]['ocultacao_css'])
 def test_tachado_tags_e_css(self):
  self.assertTrue(normative(run('<s>revogado</s>'))[0]['tags_s_del_strike']);self.assertTrue(normative(run('<p style="text-decoration:line-through">revogado</p>'))[0]['tachado_css'])
 def test_area_administrativa_camara(self):self.assertFalse(normative(run('<div style="font-family:Symbol">portal</div><div class="textoNorma"><p>Artigo próprio</p></div>',lote='145')))
 def test_marcador_cadastro_administrativo(self):
  label='###DEC-001-1938@@@';r=run('<p style="font-family:Symbol">'+label+'</p>',admin={'paragrafos':[{'marcador':label}]});self.assertEqual(r['eventos_texto_efetivo_DOM'][0]['escopo'],'administrativo_comprovado');self.assertFalse(normative(r))
 def test_inline_important_vence_regra(self):self.assertFalse(normative(run('<p class="x" style="font-family:Arial!important">normal</p>','<style>.x{font-family:Symbol!important}</style>')))
 def test_pseudo_separado(self):
  r=run('<p class="x">texto</p>','<style>.x:before{font-family:Symbol;content:"F"}</style>');self.assertTrue(r['pseudo_elementos_com_match']);self.assertFalse(normative(r))
 def test_regra_media_nao_declarada_efetiva(self):
  r=run('<p class="x">texto</p>','<style>@media print{.x{font-family:Symbol}}</style>');self.assertTrue(r['regras_condicionais_com_match']);self.assertFalse(normative(r))
if __name__=='__main__':unittest.main(verbosity=2)
