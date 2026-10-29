from pathlib import Path
import sys,unittest,json,gzip,re
B=Path(__file__).resolve().parent;R=B.parents[3];C=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo';sys.path[:0]=[str(B),str(C),str(R/'scripts/bin/qa-html5-20261027/python')]
from escopo_DOM import conferir
from gate_orgao_contextual import motivos
class Escopo(unittest.TestCase):
 def source(self,body='<p>Art. 1º Taxa de 0,5%.</p>',extra=''):
  frag='<div class="texto-dou">'+body+'</div>'+extra
  return '<html><body><main>'+frag+'<div class="rodape">Logo</div></main></body></html>',frag
 def test_cargo_assinatura_e_aviso_preservados(self):
  s,f=self.source(extra='<p class="assina">Maria</p><p class="cargo">Substituta</p><div class="informacao-conteudo-dou">Este conteúdo não substitui o publicado na versão certificada.</div>');self.assertEqual(len(conferir(s,f)['irmaos_externos_integrais']),3)
 def test_decimal_nao_colapsa(self):
  s,f=self.source()
  with self.assertRaises(AssertionError):conferir(s,f.replace('0,5','05'))
 def test_artigo_omitido(self):
  s,f=self.source('<p>Art. 1º Primeiro.</p><p>Art. 2º Segundo.</p>')
  with self.assertRaises(AssertionError):conferir(s,f.replace('<p>Art. 2º Segundo.</p>',''))
 def test_span_de_tabela_muda(self):
  s,f=self.source('<table><tr><td colspan="2">R$ 10,00</td></tr></table>')
  with self.assertRaises(AssertionError):conferir(s,f.replace('colspan="2"','colspan="1"'))
 def test_lista_inicio_muda(self):
  s,f=self.source('<ol type="I" start="3"><li>Item</li></ol>')
  with self.assertRaises(AssertionError):conferir(s,f.replace('start="3"','start="1"'))
 def test_irmao_externo_nao_administrativo_retido(self):
  s,f=self.source(extra='<section>Art. 2º Segundo documento.</section>')
  with self.assertRaises(AssertionError):conferir(s,f)
 def test_substring_falsa_nao_e_raiz(self):
  s,f=self.source()
  with self.assertRaises(AssertionError):conferir(s.replace('texto-dou','prefixo-texto-dou-falso'),f)
class Orgao(unittest.TestCase):
 def test_ministerios_intercalados_retidos(self):self.assertTrue(motivos('Ministério da Educação/Ministério da Defesa/FUNDAÇÃO UNIVERSIDADE FEDERAL DE SERGIPE','O REITOR DA UFS, resolve:'))
 def test_universidade_na_cadeia_normal_controle(self):self.assertFalse(motivos('Ministério da Educação/FUNDAÇÃO UNIVERSIDADE FEDERAL DE SERGIPE','O REITOR DA UFS, resolve:'))
 def test_autoridade_SECEX_diverge(self):self.assertTrue(motivos('Ministério do Desenvolvimento Social e Agrário/SECRETARIA DE COMÉRCIO EXTERIOR','O SECRETÁRIO DE COMÉRCIO EXTERIOR, DO MINISTÉRIODA INDÚSTRIA, COMÉRCIO EXTERIOR E SERVIÇOS,no uso de suas atribuições resolve:'))
 def test_referencia_historica_nao_e_autoridade(self):self.assertFalse(motivos('Ministério do Desenvolvimento Social e Agrário/SECRETARIA DE COMÉRCIO EXTERIOR','A PRESIDENTE DO CONSELHO, resolve: observado o Ministério da Indústria, Comércio Exterior e Serviços.'))
 def test_controle_CRSS(self):self.assertFalse(motivos('Ministério do Desenvolvimento Social e Agrário/SECRETARIA EXECUTIVA/CONSELHO DE RECURSOS DO SEGURO SOCIAL','A PRESIDENTE DO CONSELHO DE RECURSOS DO SEGURO SOCIAL, resolve:'))
 def test_tres_casos_reais(self):
  lines=gzip.decompress((B/'pacote3060_001/provas_retencoes3.jsonl.gz').read_bytes()).splitlines();self.assertEqual(len(lines),3)
  for line in lines:
   r=json.loads(line);body=r['prova_integral']['MD_utf8'].split('---',2)[2];prefix=re.split(r'\*\*Art',body,1)[0];self.assertTrue(motivos(r['registro']['meta']['orgao'],prefix),r['registro']['path'])
if __name__=='__main__':unittest.main(verbosity=2)
