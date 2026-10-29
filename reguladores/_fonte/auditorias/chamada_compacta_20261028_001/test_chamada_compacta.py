from pathlib import Path
import sys,json,gzip,unittest
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B));from gate_chamada_compacta import chamadas
class ChamadaCompacta(unittest.TestCase):
 def test_real804_exige_revisao(self):
  r=next(json.loads(l)for l in gzip.decompress((B/'provas_delta8000.jsonl.gz').read_bytes()).splitlines()if'20162170'in json.loads(l)['registro']['path']);self.assertTrue(chamadas(r['MD_utf8']));self.assertFalse(chamadas(r['MD_utf8'])[0]['ausencia_propria_demonstrada'])
 def test_controle_real43_prospectivo(self):r=json.loads(gzip.decompress((B/'controle_MDS43.json.gz').read_bytes()));self.assertFalse(chamadas(r['MD_utf8']))
 def test_real187_alerta_sem_inferir_ausencia(self):
  r=next(json.loads(l)for l in gzip.decompress((B/'provas_delta8000.jsonl.gz').read_bytes()).splitlines()if'20218630'in json.loads(l)['registro']['path']);self.assertTrue(chamadas(r['MD_utf8']));self.assertFalse(chamadas(r['MD_utf8'])[0]['ausencia_propria_demonstrada']);self.assertIn('POLÍTICA DE GESTÃO DE RISCOS',r['MD_utf8'])
 def test_anexo_espacado_nao_e_esta_classe_nova(self):self.assertFalse(chamadas('Art. 3º Os proprietários constantes do anexo desta Portaria devem agendar.'))
 def test_compacto_sem_espaco_antes_tipo(self):self.assertTrue(chamadas('Art. 1º Na forma do AnexodestaPortaria.'))
 def test_prospectivo_generico_nao_e_chamada(self):self.assertFalse(chamadas('Art. 1º A lista será divulgada a cada exercício no sítio eletrônico.'))
 def test_futura_publicacao_de_anexo_nao_e_chamada_deitica(self):self.assertFalse(chamadas('Art. 1º Um anexo poderá ser publicado no próximo exercício.'))
 def test_palavra_parecida_nao_e_anexo(self):self.assertFalse(chamadas('Art. 1º O caderno anexodestacado será arquivado.'))
 def test_remissao_externa_nao_e_mesmo_literal(self):self.assertFalse(chamadas('Art. 1º Aplica-se o anexo do Decreto nº 50.'))
 def test_citacao_e_alerta_nao_ausencia_demonstrada(self):self.assertFalse(chamadas('Art. 1º A expressão "anexodesta Portaria" deve ser transcrita no campo de referência.')[0]['ausencia_propria_demonstrada'])
if __name__=='__main__':unittest.main(verbosity=2)
