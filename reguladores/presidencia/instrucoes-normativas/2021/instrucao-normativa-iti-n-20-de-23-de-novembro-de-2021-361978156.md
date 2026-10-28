---
titulo: "INSTRUÇÃO NORMATIVA ITI Nº 20, DE 23 DE NOVEMBRO DE 2021"
orgao: "Presidência da República/Casa Civil/Instituto Nacional de Tecnologia da Informação"
tipo: "Instrução Normativa"
numero: "20"
data: 2021-11-23
revogada: null
versao_texto: "publicação original"
publicacao: "DOU de 25/11/2021, seção 1, p. 5"
data_publicacao: 2021-11-25
edicao: "221"
fonte: "https://www.in.gov.br/web/dou/-/instrucao-normativa-iti-n-20-de-23-de-novembro-de-2021-361978156"
sha256_html_fonte: 3fb74a38bb000b1df10d3f462b0cce46615e0b07a2aad9cdfecaefccb0c14abe
baixado_em: 2026-10-21
---
# INSTRUÇÃO NORMATIVA ITI Nº 20, DE 23 DE NOVEMBRO DE 2021

INSTRUÇÃO NORMATIVA ITI Nº 20, DE 23 DE NOVEMBRO DE 2021

Aprova a revisão e a consolidação dos regulamentos de envio de informações e arquivos ao Instituto Nacional de Tecnologia da Informação - ITI.

**O DIRETOR-PRESIDENTE DO INSTITUTO NACIONAL DE TECNOLOGIA DA INFORMAÇÃO**, no uso das atribuições que lhe foram conferidas pelo inciso VI do art. 9° do anexo I do Decreto n° 8.985, de 8 de fevereiro de 2017, e pelo art. 1° da Resolução n° 33, do Comitê Gestor da ICP-Brasil, de 21 de outubro de 2004, e pelo art. 2° da Resolução n° 163 do Comitê Gestor da ICP-Brasil, de 17 de abril de 2020,

CONSIDERANDO a determinação estabelecida pelo Decreto n° 10.139, de 28 de novembro de 2019, para revisão e consolidação dos atos normativos inferiores a decreto, editados por órgãos e entidades da administração pública federal direta, autárquica e fundacional, resolve:

**Art. 1º** Esta Instrução Normativa Regulamenta o envio de informações e arquivos ao Instituto Nacional de Tecnologia da Informação - ITI.

**Parágrafo único.** O disposto nesta Instrução Normativa não se aplica ao Cadastro de Agentes de Registos - CAR, que possui regulamentação própria.

**Art. 2º** Todas as Autoridades Certificadoras - ACs que emitem certificados digitais para usuário final deverão enviar semanalmente ao Instituto Nacional de Tecnologia da Informação - ITI, toda segunda-feira da semana seguinte à respectiva emissão, os certificados emitidos, as biometrias atreladas a cada certificado e informações sobre suas emissões.

**Parágrafo único.** Nos casos em que o dia do envio corresponder a feriado, a remessa dos certificados deverá ser realizada no dia útil seguinte.

**Art. 3º** As informações referentes às emissões deverão conter, para cada certificado emitido, o hash SHA1 do arquivo do certificado, codificado em DER, associado com a identificação do município onde ocorreu a identificação presencial do titular do certificado, conforme formato definido no Anexo, em arquivo identificado com nome Anexo1.csv.

**§ 1º** Na identificação do município deve ser utilizado o correspondente código de município definido pelo Instituto Brasileiro de Geografia e Estatística - IBGE.

**§ 2º** Nos casos de identificação presencial do titular do certificado ocorrida em localidades fora do Brasil, fica estabelecido como código de Município o numeral 90 (noventa), acrescido da codificação numérica de país definida pela ISO 3166, com 3 (três) dígitos numéricos. Exemplos: EUA=90840; Portugal=90620.

**§ 3º** Os certificados, por sua vez, deverão ser identificados e encaminhados individualmente, utilizando a codificação DER (\*.cer).

**§ 4º** Os arquivos biométricos da face e das impressões digitais deverão ter os formatos e a indicação do dedo, se for o caso, conforme disposto no DOC-ICP-05.02 e no DOC-ICP-05.03, seguindo as definições dispostas no ADE-ICP-05.C.

**§ 5º** As informações, os certificados e os arquivos biométricos deverão ser encaminhados ao ITI em um arquivo compactado (.zip), por meio do carregamento do arquivo (upload) dentro da respectiva área de transferência de arquivos da AC (FTP).

**§ 6º** O nome do arquivo compactado e o procedimento de envio devem seguir as orientações dispostas no ADE-ICP-05.C.

Art. 4ºAnualmente, até o dia 15 de dezembro, em conformidade com o DOC-ICP-08, as Autoridades Certificadoras - ACs, Autoridades de Carimbo do Tempo - ACTs, Prestadores de Serviços Biométricos - PSBios e Prestadores de Serviços de Confiança - PSCs devem encaminhar ao ITI o Plano Anual de Auditoria Operacional - PLAAO.

**§ 1º** As informações devem ser encaminhadas ao ITI em um arquivo no formato zip contendo o arquivo pdf do ADE-ICP-08.C e as informações referentes ao PLAAO em arquivo CVS.

**§ 2º** O arquivo compactado deve ser identificado com nome PLAAO\_ANO\_nome da entidade na ICP-Brasil.zip.

**§ 3º** O arquivo CSV deve seguir as instruções de formato de arquivo e preenchimento dos campos definidas no anexo desta Instrução Normativa.

**§ 4º** O arquivo compactado deve ser encaminhado para o e-mail plaao@iti.gov.br.

**Art. 5º** As informações referentes ao PLAAO de AC deverão conter, para cada entidade vinculada, as seguintes informações:

I - nome da AC responsável pelo preenchimento das informações;

II - número do CNPJ da entidade vinculada à AC responsável pelo preenchimento;

III - nome da entidade vinculada à AC responsável pelo preenchimento;

IV - data prevista para o início da auditoria na respectiva instalação técnica;

V - data prevista para entrega do relatório de auditoria pela entidade responsável pela execução da auditoria;

VI - CNPJ da empresa que realizará a auditoria; e

VII - informações adicionais que a AC julgar conveniente apresentar.

**Parágrafo único.** O arquivo CSV deve ser identificado com nome PLAAOANO\_nome da AC na ICP-Brasil.csv.

**Art. 6º** As informações referentes ao PLAAO de ACT, PSBio e PSC deverão conter, para cada entidade vinculada, as seguintes informações:

I - nome da ACT ou PSBio ou PSC responsável pelo preenchimento das informações;

II - data prevista para o início da auditoria nas respectivas entidades;

III - data prevista para entrega do relatório de auditoria pela entidade responsável pela execução da auditoria;

IV - CNPJ da empresa que realizará a auditoria; e

V - informações adicionais que a entidade julgar conveniente apresentar.

**Parágrafo único.** O arquivo CSV deve ser identificado com nome PLAAO\_ANO\_nome da entidade na ICP-Brasil.csv.

**Art. 7º** As entidades de auditoria devem encaminhar ao ITI relatórios e informações de auditoria em até 15 dias após a data prevista no PLAAO para a entrega do relatório de auditoria, contendo, para cada entidade auditada, as seguintes informações:

I - para Relatório de AR

a) CNPJ da entidade de auditoria responsável pelo preenchimento das informações;

b) ome na ICP-Brasil da entidade auditada, seguido de dois pontos ":" e número do CNPJ;

c) nome das ACs vinculada à AR auditada, separado por virgula, ex: AC xxxx rfb,AC XXXXX multipla;

d) ano da auditoria prevista no PLAAO;

e) data prevista para o início da auditoria na respectiva entidade;

f) data do relatório;

g) Conceito Geral atribuído à entidade auditada; e

h) relação das não conformidade identificadas.

II - para Relatório de AC e PSS

a) CNPJ da entidade de auditoria responsável pelo preenchimento das informações;

b) nome na ICP-Brasil da entidade auditada, seguido de dois pontos ":" e número OID da DPC da AC auditada preenchido sem ponto, exemplo: AC TESTE:21676110;

c) nome da entidade superior vinculada à AC auditada, ex: AC RAIZ ou AC RFB;

d) ano da auditoria prevista no PLAAO;

e) data prevista para o início da auditoria na respectiva entidade;

f) data do relatório;

g) Conceito Geral atribuído à entidade auditada; e

h) relação das não conformidade identificadas.

III - para Relatório de ACT, PSC e PSBio

a) CNPJ da entidade de auditoria responsável pelo preenchimento das informações, preenchido sem ponto ou barra ou hífen (ex: 99999999999999);

b) nome na ICP-Brasil da entidade auditada, seguido de dois pontos ":" e número do preenchido sem ponto ou barra ou hífen (ex: 99999999999999);

c) tipo de entidade auditada, ACT ou PSBio ou PSC;

d) ano da auditoria prevista no PLAAO;

e) data prevista para o início da auditoria na respectiva entidade;

f) data do relatório;

g) Conceito Geral atribuído a entidade auditada; e

h) relação das não conformidade identificadas.

**§ 1º** Os relatórios de auditoria devem ser no formato PDF, assinados digitalmente com certificado ICP-Brasil pelo responsável técnico da entidade de auditoria.

**§ 2º** As informações sobre o relatório de auditoria devem ser encaminhadas ao ITI em arquivo no formato CSV, conforme formato definido no Anexo, identificado com o nome rel\_ano do relatório\_nome da entidade auditada.csv.

**§ 3º** O relatório (PDF) e as informações (CSV) devem ser incluídos em um único arquivo compactado (.zip) e encaminhados para o e-mail relatorio.auditoria@iti.gov.br.

**Art. 8º** Ficam revogadas:

I - Instrução Normativa n° 05, de 16 de julho de 2019; e

II - Instrução Normativa n° 06, de 05 de agosto de 2019.

**Art. 9º** Esta Instrução Normativa entra em vigor em 1° de dezembro de 2021.

CARLOS ROBERTO FORTNER

## ANEXO I — Definições do formato dos arquivos csv

1 Formato do arquivo

Para a transferência das informações ao Instituto Nacional de Tecnologia da Informação - ITI devem ser observados os dados solicitados nos artigos específicos para cada caso, devendo ser utilizados arquivos no formato CSV.

CSV é a abreviação do termo em inglês*Comma-Separated Values*, que pode ser traduzido para o português como "Valores separados por vírgulas", e é constituído de um arquivo de texto cujas informações contidas estão separadas por ponto e vírgula. Exemplo: Fulano de Tal;23/10/1983;Maria de Tal.

Normalmente, a extensão do arquivo utilizada nesses casos é ".csv" e refere-se a um formato de arquivo de dados definido na RFC 4180, sendo suportado pela maioria dos softwares de planilha eletrônica e Sistemas Gerenciadores de Banco de Dados - SGDB. Além disso, é recomendado pelo Padrão de Interoperabilidade de Governo Eletrônico - ePing e utilizado pelo Portal da Transparência do Governo Federal.

No caso dos arquivos CSV que devem ser encaminhados ao ITI, cada linha deve conter uma unidade de informação. Para atender o art. 3°, por exemplo, a linha deve conter o hash SHA1 do arquivo do certificado e a identificação do município onde ocorreu a identificação presencial do titular do certificado, separados por ponto e vírgula.

A inclusão de uma linha inicial com os nomes de cada campo é opcional, mas a ordem dos campos deve seguir rigorosamente a ordem solicitada em cada caso.

O ponto e vírgula deverá constar mesmo quando o campo correspondente não for preenchido. Exemplo: 1234;5678;;;91011. Nesse caso, dois campos foram deixados sem preenchimento. Importante observar que a linha não pode terminar em ponto e vírgula, exceto se a informação do último campo estiver vazia.

Para evitar problemas de compatibilidade na codificação dos caracteres, os arquivos encaminhados ao ITI devem utilizar a codificação UTF-8 ISO/IEC 10646:2014, recomendada pelo ePing.

2 Formatação dos campos

Em cada caso, quando solicitado, devem ser observados as orientações abaixo para o preenchimento dos campos.

Código IBGE: O código IBGE do município está disponível no site do IBGE e deve ser informado com sete dígitos, por exemplo, para Brasília deve ser informado o código 5300108. Excepcionalmente, para emissões realizadas no localidades fora do Brasil, fica estabelecido como código de Município o numeral 90 (noventa), acrescido da codificação numérica de país definida pela ISO 3166, com 3 (três) dígitos numéricos. Exemplos: EUA=90840; Portugal=90620.

CNPJ: O número do Cadastro Nacional de Pessoa Jurídica deve ser informado com 14 dígitos sem os separadores. Exemplo: o CNPJ 99.999.999/9999-99 deve ser informado 99999999999999.

Data: as informações de data devem ser preenchidas no formato dd/mm/aaaa. Exemplo: para a data de 12 de setembro de 2016 deve ser informado 12/09/2016.

Ano: a informação de ano deve ser preenchida no formato aaaa, ou seja, sempre com os quatro números que compões essa informação, exemplos: 1999, 2000, 2021, 2022, etc.

Relação das não conformidades identificadas: código do controle constante do ADE\_ICP 08.e, dois pontos e descrição da não conformidade conforme consta do relatório de auditoria. Ex: 20601002:Fragilidade nas atualizações do sistema operacional. Caso tenha uma não conformidade que envolva vários itens do ADE\_ICP 08.e, deve ser lançado o código do item mais relevante ou principal.

Número do OID da DPC da AC: Os números de identificação de cada DPC das AC credenciadas na ICP-Brasil estão disponíveis no documento ADE-ICP-04.01, no arco 2.16.76.1.1. No preenchimento dos campos de OID no arquivo CVS devem ser retirados os pontos separadores, assim, o OID 2.16.76.1.1.0 deve ser informado como 21676110.
