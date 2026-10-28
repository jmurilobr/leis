"""Gates privados: tabela HTML5 por linha e risco visual sem inferência jurídica."""
from pathlib import Path
import copy
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from auditar_dou_css_tabelas_privado_20261027 import matrizes,riscos,ROOT


class AuditoriaPrivada(unittest.TestCase):
    def test_oculto_tachado_e_css_contextual(self):
        for f in ['<p hidden>A</p>','<p aria-hidden="true">A</p>',
                  '<p style="visibility:hidden">A</p>','<del>A</del>',
                  '<p style="text-decoration:line-through">A</p>']:
            self.assertTrue(riscos('<div class="texto-dou">'+f+'</div>',''))
        self.assertTrue(riscos('<div class="texto-dou"><p class="x">A</p></div>',
                               '<style>.x {display:none}</style>'))
        self.assertFalse(riscos('<div class="texto-dou"><p>A - 0,5%.</p></div>',''))

    def test_mesmas_celulas_globais_em_linhas_diferentes_nao_passam(self):
        a,_=matrizes('<table><tr><td>A</td><td>B</td></tr><tr><td>C</td></tr></table>')
        b,_=matrizes('<table><tr><td>A</td></tr><tr><td>B</td><td>C</td></tr></table>')
        self.assertEqual([c['texto'] for t in a for r in t for c in r],
                         [c['texto'] for t in b for r in t for c in r])
        self.assertNotEqual(a,b)

    def test_mesclagem_e_papel_celula_preservados_no_comparador(self):
        a,_=matrizes('<table><tr><td colspan="2" rowspan="2">0</td></tr></table>')
        b=copy.deepcopy(a);b[0][0][0]['colspan']='1'
        self.assertNotEqual(a,b)
        b=copy.deepcopy(a);b[0][0][0]['tag']='th'
        self.assertNotEqual(a,b)

    def test_caso_real_11997_contra_unica_resposta_github(self):
        base=ROOT/'municipais/_indice/_recuperacao_20261027'
        source=(base/'dou11997-v2-final/fragmento-oficial.html').read_text()
        raw=(base/'dou11997-github/response.http').read_bytes()
        response=re.split(rb'\r?\n\r?\n',raw,1)[1].decode()
        a,_=matrizes(source);b,_=matrizes(response)
        self.assertEqual(a,b)
        self.assertEqual([len(t) for t in a],[120,133,125,96])


if __name__=='__main__':unittest.main()
