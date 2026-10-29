import unittest,gzip,tempfile,hashlib
from pathlib import Path
from observacao_catalogo_to import observacao_catalogo
from coletar_to_portal_indice import parse
SHA=lambda b:hashlib.sha256(b).hexdigest()
class Catalogo(unittest.TestCase):
    def row(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        raw='<div>Registros encontrados: 1<div class="row"><div class="col-12"><h4><a href="/arquivo/999">Lei nº 123 de 2020 (ordinária)</a></h4><p><small>Categoria: Legislação Estadual</small><small> | Data: 01/01/2020</small></p></div><div><em><strong>Texto. REVOGADA PELA LEI Nº 2.</strong></em></div></div></div>'.encode()
        packed=gzip.compress(raw);p=Path(temp.name)/'index.gz';p.write_bytes(packed);_,items,_=parse(raw);item=items[0];item['indice']=dict(http=200,url='https://www.al.to.leg.br/legislacaoEstadual?documento.ano=2020',cache=str(p),sha256_cache=SHA(packed),sha256_fonte=SHA(raw))
        return dict(item=item,url=item['fonte'])
    def test_literal_sem_inferencia(self):
        row=self.row();note=observacao_catalogo(row);self.assertIn(row['item']['ementa'],note);self.assertIn('sem afirmar que a mesma nota esteja no PDF',note);self.assertIn('permanecem null',note)
    def test_ementa_modificada_falha(self):
        row=self.row();row['item']['ementa']='Revogada por suposição.'
        with self.assertRaisesRegex(ValueError,'ementa'):observacao_catalogo(row)
    def test_sem_indicacao_nao_inventa_nota(self):self.assertIsNone(observacao_catalogo(dict(item=dict(id_ALETO='1'))))
if __name__=='__main__':unittest.main()
