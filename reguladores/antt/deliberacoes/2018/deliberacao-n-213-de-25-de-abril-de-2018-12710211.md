---
titulo: "DELIBERAÇÃO Nº 213, DE 25 DE ABRIL DE 2018"
orgao: "Ministério dos Transportes, Portos e Aviação Civil/Agência Nacional de Transportes Terrestres/Diretoria Colegiada"
tipo: "Deliberação"
numero: "213"
data: 2018-04-25
revogada: null
versao_texto: "publicação original"
publicacao: "DOU de 03/05/2018, seção 1, p. 76"
data_publicacao: 2018-05-03
edicao: "84"
fonte: "https://www.in.gov.br/web/dou/-/deliberacao-n-213-de-25-de-abril-de-2018-12710211"
sha256_html_fonte: 22eed342506f08697a55c8d8f82bb9bb2cf6e0b34734dadb84b478e36b7de31c
baixado_em: 2026-10-27
---
# DELIBERAÇÃO Nº 213, DE 25 DE ABRIL DE 2018

DELIBERAÇÃO Nº 213, DE 25 DE ABRIL DE 2018

A Diretoria Colegiada da Agência Nacional de Transportes Terrestres - ANTT, no uso das atribuições que lhe confere o art. 25 do Regimento Interno, aprovado pela Resolução nº 3.000, de 28 de janeiro de 2009, fundamentada no Voto DSL - 109, de 23 de abril de 2018, e no que consta do Processo nº 50500.499242/2017-32, delibera:

**Art. 1º** Alterar o Anexo da Deliberação nº 325, de 28 de setembro de 2017, que passará a vigorar com a redação do Anexo desta Deliberação.

**Art. 2º** Esta Deliberação entra em vigor na data de sua publicação.

MÁRIO RODRIGUES JÚNIOR

Diretor-Geral

## ANEXO

Número de averbação

O número de averbação do seguro é formado da seguinte forma:

I - Código SUSEP,

II - Mês/Ano Apólice,

III - CNPJ Emissor,

IV - Modelo,

V - Série,

VI - Número,

VII - Código da Empresa Averbação,

VIII - Dígito Verificador (DV).

A seguir são apresentadas as descrições dos campos:

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Campos</p> 			</td> 			<td> 			<p>Tipo</p> 			</td> 			<td> 			<p>Tamanho</p> 			</td> 			<td> 			<p>Descrição</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Código SUSEP seguradora</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>Código SUSEP da seguradora, COM o digito verificador</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Mês/Ano (mmyy) Apólice</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>Mês e ano da vigência final da apólice: mmyy. Exemplo: Apólice encerra 22/05/2017= 0517</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>CNPJ Emissor do documento</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>14</p> 			</td> 			<td> 			<p>CNPJ Emissor do documento</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Modelo</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>Código do Modelo do Documento Fiscal SEFAZ (57-CTe ou 55-NFe ou 99-Outros)</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Série</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> </td> 			<td> 			<p>Caso não informado valor padrão=001, preencher com zeros a esquerda caso tamanho menor que 3</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> </td> 			<td> 			<p>Número do Documento. Deve ser preenchido com zeros a esquerda caso tamanho menor que 9</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Código da Empresa</p>  			<p>Averbação</p> 			</td> 			<td> 			<p>Alfanumérico</p> 			</td> 			<td> </td> 			<td> 			<p>Exemplo: 1- AT&amp;M, 2- QUORUM, 3-GUEP, 4-ELT.... Utilizar "0" quando for a própria seguradora.</p> 			</td> 		</tr> 		<tr> 			<td> </td> 			<td> 			<p>Total</p> 			</td> 			<td> </td> 			<td> 			<p>-</p> 			</td> 		</tr> 	</tbody> </table>

Cálculo do dígito verificador

O Dígito Verificador (DV) irá garantir a integridade do número, protegendo principalmente contra digitações erradas.

O DV é baseado em um cálculo do módulo 11. O módulo 11 de um número é calculado multiplicando-se cada algarismo pela sequência de multiplicadores 1,2,3,4,5,6,7,8,9,1,2,3, ... posicionados da direita para a esquerda.

A somatória dos resultados das ponderações dos algarismos é dividida por 11 e o DV será a diferença entre o divisor (11) e o resto da divisão:

DV = 11 - (resto da divisão).

Quando o resto da divisão for 0 (zero) ou 1 (um), o DV deverá ser igual a 0 (zero).

Nesse contexto, deve-se considerar que a sequência para o cálculo do DV é: Código da Empresa de Averbação, Número, Modelo, Série, CNPJ Emissor, Código SUSEP, Mês/Ano Apólice.

Para ilustrar os cálculos, é apresentado um exemplo a partir da tabela abaixo.

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Sequência para cálculo do DV</p> 			</td> 			<td> 			<p>Exemplo</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Código da Empresa de Averbação</p> 			</td> 			<td> 			<p>1</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>000023437</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Modelo</p> 			</td> 			<td> 			<p>57</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Série</p> 			</td> 			<td> 			<p>889</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>CNPJ Emissor do documento</p> 			</td> 			<td> 			<p>09526131000181</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Código SUSEP seguradora</p> 			</td> 			<td> 			<p>00000</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Mês/Ano Apólice</p> 			</td> 			<td> 			<p>1217</p> 			</td> 		</tr> 	</tbody> </table>

Da tabela acima tem-se que o número para geração do módulo, conforme o exemplo é (Código da Empresa de Averbação, Número, Modelo, Série, CNPJ Emissor, Código SUSEP, Mês/Ano Apólice).

Para gerar o DV, deve-se inverter o CNPJ do Emissor no "número para geração do modulo", como demonstrado abaixo.

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Número</p>  			<p>(a)</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>7</p> 			</td> 		</tr> 	</tbody> </table>

Distribuição de cada unidade do número da averbação e multiplique pelo peso conforme abaixo:

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Número (a)</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>7</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Peso (b)</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Resultado</p>  			<p>(c) =a x b</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>12</p> 			</td> 			<td> 			<p>15</p> 			</td> 			<td> 			<p>16</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>14</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>63</p> 			</td> 			<td> 			<p>64</p> 			</td> 			<td> 			<p>56</p> 			</td> 			<td> 			<p>54</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>32</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>21</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>30</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>15</p> 			</td> 			<td> 			<p>18</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>7</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Soma do resultado (linha c)</p> 			</td> 			<td> 			<p>475</p> 			</td> 		</tr> 	</tbody> </table>

Deve-se somar os resultados da linha (c) e dividir por 11. Considera-se o resto da divisão como responsável pelo cálculo do primeiro dígito verificador.

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Soma do resultado - linha (c)</p> 			</td> 			<td> 			<p>475</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Divisão por 11</p> 			</td> 			<td> 			<p>475/11 = 43,18182</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Resto da divisão</p> 			</td> 			<td> 			<p>2</p> 			</td> 		</tr> 	</tbody> </table>

Caso o resto da divisão seja menor do que 2 deve ser assumido como primeiro dígito verificador valor '0', caso contrário subtrai-se o valor obtido de 11. Assim, conforme o exemplo tem-se que:

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Primeiro Dígito</p> 			</td> 			<td> 			<p>11-2 = 9</p> 			</td> 		</tr> 	</tbody> </table>

Para calcular o segundo dígito deve-se distribuir cada unidade do número da averbação com o primeiro dígito verificador ao final e multiplicar pelo peso conforme representação abaixo:

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Número</p>  			<p>(a)</p> 			</td> 			<td> 			<p>Número</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>(DV)9</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Peso (b)</p> 			</td> 			<td> 			<p>Peso</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>2</p> 			</td> 			<td> 			<p>1</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Resultado</p>  			<p>(c= a x b)</p> 			</td> 			<td> 			<p>Resultado</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>14</p> 			</td> 			<td> 			<p>18</p> 			</td> 			<td> 			<p>20</p> 			</td> 			<td> 			<p>12</p> 			</td> 			<td> 			<p>21</p> 			</td> 			<td> 			<p>10</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>72</p> 			</td> 			<td> 			<p>64</p> 			</td> 			<td> 			<p>63</p> 			</td> 			<td> 			<p>6</p> 			</td> 			<td> 			<p>40</p> 			</td> 			<td> 			<p>4</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>9</p> 			</td> 			<td> 			<p>24</p> 			</td> 			<td> 			<p>7</p> 			</td> 			<td> 			<p>36</p> 			</td> 			<td> 			<p>10</p> 			</td> 			<td> 			<p>20</p> 			</td> 			<td> 			<p>27</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>0</p> 			</td> 			<td> 			<p>5</p> 			</td> 			<td> 			<p>8</p> 			</td> 			<td> 			<p>3</p> 			</td> 			<td> 			<p>14</p> 			</td> 			<td> 			<p>9</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Soma do resultado (linha c)</p> 			</td> 			<td> </td> 			<td> 			<p>526</p> 			</td> 		</tr> 	</tbody> </table>

Em seguida deve-se somar os resultados da linha (c) e dividir por 11. Considere o resto da divisão como responsável pelo cálculo do primeiro dígito verificador.

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Soma do resultado - linha (c)</p> 			</td> 			<td> 			<p>526</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Divisão por 11</p> 			</td> 			<td> 			<p>47,81818</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Resto da divisão</p> 			</td> 			<td> 			<p>9</p> 			</td> 		</tr> 	</tbody> </table>

Caso o resto da divisão seja menor do que 2 deve-se assumir como primeiro dígito verificador o valor '0', caso contrário deve-se subtrair o valor obtido de 11

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Segundo Digito</p> 			</td> 			<td> 			<p>11 - 9 =2</p> 			</td> 		</tr> 	</tbody> </table>

Logo, tem-se que:

<table> 	<tbody> 		<tr> 		</tr> 		<tr> 			<td> 			<p>Número da averbação sem DV</p> 			</td> 			<td> 			<p>00000121709526131000181578890000234371</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>DV</p> 			</td> 			<td> 			<p>92</p> 			</td> 		</tr> 		<tr> 			<td> 			<p>Número da averbação com DV</p> 			</td> 			<td> 			<p>0000012170952613100018157889000023437192</p> 			</td> 		</tr> 	</tbody> </table>
