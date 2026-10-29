import unittest,io,gzip,json,hashlib
from reportlab.pdfgen import canvas
import test_to_pdf_simples as fixture
from auditar_to_pdf_simples import auditar
from metadados_to_pdf import criar,VERSAO_REFERENCIAS
from ocorrencias_alteracao_to import conferir_ocorrencias
SHA=lambda b:hashlib.sha256(b).hexdigest()
class Ocorrencias(unittest.TestCase):
    def test_nao_chama_dispositivo_de_nota_editorial(self):
        text='Art. 1º Aplica-se a redação dada pela Lei anterior.\n'
        r=conferir_ocorrencias(text);self.assertFalse(r['anotacoes_editoriais']);self.assertEqual(r['referencias_alteracao_textuais'][0]['trecho_literal'],text.rstrip('\n'));self.assertTrue(r['referencias_alteracao_textuais'][0]['natureza_juridica_nao_classificada'])
    def test_separa_marcador_literal(self):
        r=conferir_ocorrencias('(Revogada pela Lei 2.)\nArt. 1º A redação dada pela Lei 3 vale...\n')
        self.assertEqual(len(r['anotacoes_editoriais']),1);self.assertEqual(len(r['referencias_alteracao_textuais']),1)
    def test_pdf_integral_e_rotulo_sem_inferencia(self):
        case=fixture.PDFTO(methodName='test_preserva_numero_zero_decimal_negativo');case.setUp();self.addCleanup(case.doCleanups);row=case.row('simples')
        out=io.BytesIO();c=canvas.Canvas(out);t=c.beginText(60,780);t.setFont('Helvetica',11)
        for line in ['LEI Nº 123, DE 1 DE JANEIRO DE 2020.','O Governador do Estado do Tocantins','Faço saber que a Assembleia decreta e eu sanciono a seguinte Lei:','Art. 1º Aplica-se a redação dada pela norma anterior: R$ -100,00 e 0,5%.','Art. 2º Esta Lei entra em vigor na data de sua publicação.','Palácio Araguaia, em Palmas, aos 1 dias do mês de janeiro de 2020;','NOME LITERAL','Governador do Estado']:t.textLine(line)
        c.drawText(t);c.save();raw=out.getvalue();packed=gzip.compress(raw);__import__('pathlib').Path(row['cache']).write_bytes(packed);row.update(sha256_cache=SHA(packed),sha256_fonte=SHA(raw),capturado_em='2026-10-28T12:00:00-03:00')
        body,q=auditar(row);self.assertFalse(q['anotacoes_editoriais']);self.assertTrue(q['referencias_alteracao_textuais']);blob=criar(row,q,body).decode();header,actual=blob[4:].split('\n---\n',1);meta=dict((k,json.loads(v)) for k,v in (ln.split(': ',1) for ln in header.splitlines()));self.assertEqual(meta['versao_texto'],VERSAO_REFERENCIAS);self.assertIsNone(meta['revogada']);self.assertIsNone(meta['situacao']);self.assertIn('-100,00 e 0,5%',actual);self.assertEqual(actual,'# '+q['epigrafe']+'\n\n'+body)
if __name__=='__main__':unittest.main()
