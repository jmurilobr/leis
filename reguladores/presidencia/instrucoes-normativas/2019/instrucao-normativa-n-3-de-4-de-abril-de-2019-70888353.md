---
titulo: "INSTRUÇÃO NORMATIVA Nº 3, DE 4 DE ABRIL DE 2019"
orgao: "Presidência da República/Casa Civil/Instituto Nacional de Tecnologia da Informação"
tipo: "Instrução Normativa"
numero: "3"
data: 2019-04-04
revogada: null
versao_texto: "publicação original"
publicacao: "DOU de 10/04/2019, seção 1, p. 3"
data_publicacao: 2019-04-10
edicao: "69"
fonte: "https://www.in.gov.br/web/dou/-/instrucao-normativa-n-3-de-4-de-abril-de-2019-70888353"
sha256_html_fonte: 52d3865d71af63f048f04bbd011c6ff424aa20b24e46552b9f4e5bfb1a27e340
baixado_em: 2026-10-21
---
# INSTRUÇÃO NORMATIVA Nº 3, DE 4 DE ABRIL DE 2019

**INSTRUÇÃO NORMATIVA Nº 3, DE 4 DE ABRIL DE 2019**

Atualiza os requisitos para serviços de confiança de uso de chaves privadas.

**O DIRETOR-PRESIDENTE DO INSTITUTO NACIONAL DE TECNOLOGIA DA INFORMAÇÃO**, no uso das atribuições que lhe foram conferidas pelo inciso VI do art. 9º do anexo I do Decreto nº 8.985, de 8 de fevereiro de 2017, e pelo art. 1º da Resolução nº 33 do Comitê Gestor da ICP-Brasil, de 21 de outubro de 2004, resolve:

**Art. 1º** A alínea "a" do item 6.4.5.2 do DOC-ICP-17.01, versão 2.0, passa a vigorar com a seguinte redação:

"................................................................................................................................

a) Solicitação

Path: &lt;URI-base>/oauth/signature

Método HTTPS: POST

Cabeçalho: Re: Nova Versão da IN PSC

Content-type: application/json;

Accept : application/json;

Authorization: Bearer*access\_token;*

Parâmetros: formato "application/json;charset=UTF-8":

certificate\_alias: opcional, identificador do certificado correspondente à chave utilizada na assinatura;

hashes: conjunto com valores a serem assinados. Cada elemento do conjunto conterá:

id: identificador do conteúdo a ser assinado;

alias: forma legível do identificador do conteúdo;

hash: conteúdo a ser assinado;

hash\_algorithm: Object Identifier (OID) do algoritimo de hash. Por exemplo, para SHA256 utilize o OID 2.16.840.1.101.3.4.2.1;

signature\_format: obrigatório:

RAW: resultado direto (em base64) da operação RSA/DSA sobre o hash informado na requisição.

CMS detached (PKCS#7), contendo os seguintes atributos assinados:

\- contentType

\- signingTime (hora do PSC)

\- messageDigest (hash informado pela aplicação na requisição)

\- signingCertificateV2 (certificado do assinante)

Exemplo

*"hashes": [{*

"id": "Signature request ID 1",

"alias": "Contrato de aluguel XPTO",

"hash": "hash to sign",

"hash\_algorithm": "2.16.840.1.101.3.4.2.1",

"*signature\_format": "RAW"*

},

{

"id": "Signature request ID 2",

"alias": "Documento do Word",

"hash": "hash to sign",

"hash\_algorithm": "2.16.840.1.101.3.4.2.1",

"*signature\_format": "CMS"*

}

{

"id": "Signature request ID n",

"alias": "Firefox",

"hash": "hash to sign",

"hash\_algorithm": "2.16.840.1.101.3.4.2.1",

"*signature\_format" : "RAW"*

}

]}

......................................................................................................................." (NR)

**Art. 2º** A alínea "a" do item 6.4.5.5 do DOC-ICP-17.01, versão 2.0, passa a vigorar com a seguinte redação:

"6.4.5.5. Recuperação de Certificado

Serviço para recuperar certificado armazenado no PSC.

A aplicação deverá ter um Access Token de usuário válido.

a) .............................................................................................................................

......................................................................................................................." (NR)

**Art. 3º** A alínea "a" do item 6.4.5.6 do DOC-ICP-17.01, versão 2.0, passa a vigorar com a seguinte redação:

"................................................................................................................................

a) Solicitação

Path: &lt;URI-base>/oauth/user-discovery;

Método HTTPS: POST;

Parâmetros da requisição: formato "application/json;charset=UTF-8":

client\_id: obrigatório, deve conter a identificação da aplicação;

client\_secret: obrigatório, deve conter o segredo associado à aplicação;

user\_cpf\_cnpj: obrigatório, deve conter "CPF" para pessoa física ou"CNPJ" pessoa jurídica;

val\_cpf\_cnpj: obrigatório, deve conter o valor do cpf ou cnpj.

........................................................................................................................" (NR)

**Art. 4º** A alínea "a" do item 6.4.6.2.1 do DOC-ICP-17.01, versão 2.0, passa a vigorar com a seguinte redação:

"................................................................................................................................

a) Solicitação

Método HTTPS : POST;

Path: &lt;URI-base>/oauth/client\_token;

Parâmetros da requisição: formato "application/x-www-form-urlencoded":

grant\_type, obrigatório, valor "client\_credentials";

client\_id, obrigatório, deve conter a identificação da aplicação;

client\_secret, obrigatório para aplicações que possuem certificado digital;

Exemplo

*POST {.../oauth/client\_token} HTTP/1.1*

Host: {servidor do PSC}

Content-Type: application/x-www-form-urlencoded

client\_id=Identificacao\_aplicacao

&client\_secret=123qwe

&grant\_type=client\_credentials

......................................................................................................................." (NR)

**Art. 5º** Aprovar a versão 2.1 do documento DOC-ICP-17.01 - PROCEDIMENTOS OPERACIONAIS MÍNIMOS PARA OS PRESTADORES DE SERVIÇO DE CONFIANÇA DA ICP-BRASIL.

**§ 1º** As demais cláusulas do referido documento, na sua versão imediatamente anterior, integram a presente versão e mantêm-se válidas.

**§ 2º** O documento referido no caput encontra-se disponibilizado, em sua totalidade, no sítio http://www.iti.gov.br.

**Art. 6º** Esta Instrução Normativa entra em vigor na data de sua publicação.

MARCELO AMARO BUZ
