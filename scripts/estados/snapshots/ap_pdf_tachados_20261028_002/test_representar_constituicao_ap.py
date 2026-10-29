import unittest
from representar_constituicao_ap import marcar,material_nao_tachado,MODO
from verificar_motores_ap import comparar

class Representacao(unittest.TestCase):
    def test_negrito_link_lista_e_sinais(self):
        old='**igual** igual\n\n- [igual](https://example.org)\n- atual R$ -100,00; 0,5%\n'
        new='<del>**igual**</del> igual\n\n- [<del>igual</del>](https://example.org)\n- atual R$ -100,00; 0,5%\n'
        pairs=[(i,c) for i,c in enumerate('igualigualigualatualR$-100,00;0,5%') if i<5 or 10<=i<15]
        self.assertEqual(len(comparar(old,new,pairs)['combinacoes']),4)
    def test_palavra_identica_no_lugar_errado_falha(self):
        with self.assertRaisesRegex(ValueError,'posição/caractere'):
            comparar('igual igual\n','igual <del>igual</del>\n',list(enumerate('igual')))
    def test_ancestralidade_nao_pode_mudar(self):
        with self.assertRaisesRegex(ValueError,'negrito/link/lista'):
            comparar('**antigo** atual\n','<del>antigo</del> atual\n',list(enumerate('antigo')))
    def test_continuidade_e_nota_fora_do_risco(self):
        old='**Art. 3º** Antigo\n(revogado pela EC)\nII - anterior\nEMENDAS CONSTITUCIONAIS\nHistórico\n'
        selected={i for token in ['Antigo','II - anterior'] for start in [old.index(token)] for i in range(start,start+len(token)) if not old[i].isspace()}
        new,runs=marcar(old,selected)
        self.assertEqual(new.replace('<del>','').replace('</del>',''),old)
        actual=material_nao_tachado(new,MODO)
        self.assertIn('(revogado pela EC)',actual);self.assertNotIn('Antigo',actual);self.assertNotIn('Histórico',actual)
        self.assertEqual(new[new.index('EMENDAS CONSTITUCIONAIS'):],old[old.index('EMENDAS CONSTITUCIONAIS'):])
    def test_modo_desconhecido_falha(self):
        with self.assertRaises(ValueError):material_nao_tachado('texto','outro')
    def test_del_preexistente_falha(self):
        with self.assertRaises(ValueError):marcar('<del>texto</del>',{5})
    def test_unicode_stream_grande(self):
        old=('público § 1º ação; '*8000)+'final\n';new=old.replace('final','<del>final</del>')
        start=sum(not c.isspace() for c in old[:-6])
        self.assertEqual(len(comparar(old,new,[(start+i,c) for i,c in enumerate('final')])['combinacoes']),4)

if __name__=='__main__':unittest.main()
