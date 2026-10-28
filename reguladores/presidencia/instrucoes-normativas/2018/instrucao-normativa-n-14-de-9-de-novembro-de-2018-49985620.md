---
titulo: "INSTRUÇÃO NORMATIVA Nº 14, DE 9 DE NOVEMBRO DE 2018"
orgao: "Presidência da República/Casa Civil/Instituto Nacional de Tecnologia da Informação"
tipo: "Instrução Normativa"
numero: "14"
data: 2018-11-09
revogada: null
versao_texto: "publicação original"
publicacao: "DOU de 13/11/2018, seção 1, p. 8"
data_publicacao: 2018-11-13
edicao: "218"
fonte: "https://www.in.gov.br/web/dou/-/instrucao-normativa-n-14-de-9-de-novembro-de-2018-49985620"
sha256_html_fonte: ea735bcc2a3910ed8a74f772342c1966653b978139354fb9c8ae91e2cf78a593
baixado_em: 2026-10-27
---
# INSTRUÇÃO NORMATIVA Nº 14, DE 9 DE NOVEMBRO DE 2018

**INSTRUÇÃO NORMATIVA Nº 14, DE 9 DE NOVEMBRO DE 2018**

Regulamenta novas curvas elípticas e algoritmos de resumo (hash) no âmbito da ICP-Brasil

**O DIRETOR-PRESIDENTE DO INSTITUTO NACIONAL DE TECNOLOGIA DA INFORMAÇÃO**, no uso das atribuições que lhe foram conferidas pelo inciso VI do art. 9º do anexo I do Decreto nº 8.985, de 8 de fevereiro de 2017, e pelo art. 1º da Resolução nº 33, do Comitê Gestor da ICP-Brasil, de 21 de outubro de 2004,

Considerando que o art. 12 da Resolução nº 139 do Comitê Gestor da ICP-Brasil, de 03 de julho de 2018, incluiu no DOC-ICP-04, versão 6.6, a previsão de que a AC Raiz regulamentaria a curva elíptica a ser implementada pela ICP-Brasil, resolve:

**Art. 1º** A tabela "Geração de Chaves Assimétricas de AC" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Geração de Chaves Assimétricas de AC</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-01 - item 6.1.1.3</p><p>DOC-ICP-04 - item 6.1.1.3</p><p>DOC-ICP-01 - item 6.1.5</p><p>DOC-ICP-05 - item 6.1.5</p></td></tr><tr><td><p>Algoritmo</p></td><td><p>RSA ou ECC-Brainpool (conforme RFC 5639) ou Ed448-Goldilocks (conforme RFC 8032) ou E-521</p></td></tr><tr><td><p>Tamanho de chave</p></td><td><p>RSA 2048 ou RSA 4096 ou brainpoolP512r1 ou Ed448 (448 bits) ou E-521 (521 bits)</p></td></tr></table>

**Art. 2º** A tabela "Geração de Chaves Assimétricas de Usuário Final" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Geração de Chaves Assimétricas de Usuário Final</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-04 - item 6.1.5.2</p></td></tr><tr><td><p>Algoritmo</p></td><td><p>RSA ou ECC-Brainpool (conforme RFC 5639) ou Curve25519 (Conforme RFC 7748) ou Ed25519 (conforme RFC 8032) ou Ed448-Goldilocks (conforme RFC 8032) ou E-521</p></td></tr><tr><td><p>Tamanho de chave A1, A2, A3, A CF-e-SAT, S1, S2, S3, T3, OM-BR</p></td><td><p>RSA 1024 ou, RSA 2048 ou brainpoolP256r1 ou Curve25519 (256 bits) ou Ed25519 (256 bits) ou Ed448 (448 bits) ou E-521 (521 bits)</p></td></tr><tr><td><p>Tamanho da chave A4, S4, T4</p></td><td><p>RSA 2048 ou RSA 4096 ou brainpoolP512r1 ou Curve25519 (256 bits) ou Ed25519 (256 bits) ou Ed448 (448 bits) ou E-521 (521 bits)</p></td></tr></table>

**Art. 3º** A tabela "Assinatura de Certificados de AC" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Assinatura de Certificados de AC</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-01 - item 7.1.3</p><p>DOC-ICP-01 - item 7.2.3</p><p>DOC-ICP-05 - item 7.2.3</p></td></tr><tr><td><p>Suíte de Assinatura</p></td><td><p>sha1WithRSAEncryption</p><p>sha512WithRSAEncryption</p><p>sha512WithECDSAEncryption</p><p>sha512WithEdDSAEncryption</p><p>shake256WithEdDSAEncryption</p></td></tr></table>

**Art. 4º** A tabela "Assinatura de Certificados de Usuário Final" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Assinatura de Certificados de Usuário Final</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-04 - item 7.1.3</p></td></tr><tr><td><p>Suíte de Assinatura</p></td><td><p>sha1WithRSAEncryption</p><p>sha256WithRSAEncryption</p><p>sha256WithECDSAEncryption</p><p>shake256WithEdDSAEncryption</p><p>sha512WithRSAEncryption</p><p>sha512WithECDSAEncryption</p><p>sha512WithEdDSAEncryption</p></td></tr></table>

**Art. 5º** A tabela "Assinatura de Listas de Certificados Revogados e Respostas OCSP" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Assinatura de Listas de Certificados Revogados e Respostas OCSP</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-01 - item 7.3</p><p>DOC-ICP-04 - item 7.2</p><p>DOC-ICP-05 - item 7.3</p></td></tr><tr><td><p>Algoritmo de Assinatura</p></td><td><p>sha1WithRSAEncryption</p><p>sha256WithRSAEncryption</p><p>sha256WithECDSAEncryption</p><p>shake256WithEdDSAEncryption</p><p>sha512WithRSAEncryption</p><p>sha512WithECDSAEncryption</p><p>sha512WithEdDSAEncryption</p></td></tr></table>

**Art. 6º** A tabela "Assinaturas Digitais ICP-Brasil CAdES, XAdES e PAdES" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Assinaturas Digitais ICP-Brasil<em>CAdES, XAdES e PAdES</em></p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-15, item 6.1</p></td></tr><tr><td><p>Função resumo</p></td><td><p>SHA - 1</p><p>SHA - 256</p><p>SHA - 512</p><p>SHAKE - 256</p></td></tr><tr><td><p>Suíte de Assinatura</p></td><td><p>sha1WithRSAEncryption</p><p>sha256WithRSAEncryption</p><p>sha256WithECDSAEncryption</p><p>shake256WithEdDSAEncryption</p><p>sha512WithRSAEncryption</p><p>sha512WithECDSAEncryption</p><p>sha512WithEdDSAEncryption</p></td></tr></table>

**Art. 7º** A tabela "Assinatura de Pedidos e Respostas de Carimbos do Tempo" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Assinatura de Pedidos e Respostas de Carimbos do Tempo</p></td></tr><tr><td><p>Normativo ICP-Brasil</p></td><td><p>DOC-ICP-12, item 7.2</p></td></tr><tr><td><p>Função resumo</p></td><td><p>SHA - 1</p><p>SHA - 256</p><p>SHA - 512</p><p>SHAKE - 256</p></td></tr><tr><td><p>Suíte de Assinatura</p></td><td><p>sha1WithRSAEncryption</p><p>sha256WithRSAEncryption</p><p>sha256WithECDSAEncryption</p><p>shake256WithEdDSAEncryption</p><p>sha512WithRSAEncryption</p><p>sha512WithECDSAEncryption</p><p>sha512WithEdDSAEncryption</p></td></tr></table>

**Art. 8º** A tabela "Esquemas de Acordos de Chaves" do item 2 do DOC-ICP-01.01, versão 3.2, passa a vigorar com a seguinte redação:

<table><tr></tr><tr><td><p>Esquemas de Acordos de Chaves</p></td></tr><tr><td><p>ECDH256 ou ECMQV256</p></td></tr><tr><td><p>ECDH512 ou ECMQV512</p></td></tr><tr><td><p>ECDHE X25519</p></td></tr><tr><td><p>ECDHE X448</p></td></tr><tr><td><p>RSA 1024</p></td></tr><tr><td><p>RSA 2048</p></td></tr><tr><td><p>RSA 4096</p></td></tr></table>

**Art. 9º** Aprovar a versão 4.0 do documento DOC-ICP-01.01 - PADRÕES E ALGORITMOS CRIPTOGRÁFICOS DA ICP-BRASIL.

**§ 1º** As demais cláusulas do referido documento, na sua versão imediatamente anterior, integram a presente versão e mantêm-se válidas.

**§ 2º** O documento referido no caput encontra-se disponibilizado, em sua totalidade, no sítio http://www.iti.gov.br.

**Art. 10.** Esta Instrução Normativa entra em vigor na data de sua publicação.

GASTÃO JOSÉ DE OLIVEIRA RAMOS
