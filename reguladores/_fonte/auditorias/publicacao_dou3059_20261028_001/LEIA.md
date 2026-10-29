# Seleção DOU 3.059: publicação em dois blocos

A seleção efetiva é exclusivamente a dos 3.059 documentos do manifesto final de dou2017_selecao3059. Os antecedentes de 3.060 e a prova de 8.000 entradas são controles, sem acréscimo de normas. A Portaria MAPA 804 não integra nenhuma lista efetiva de normas.

Execute a partir da raiz do repositório, sem regenerar os snapshots:

```sh
python3 -I reguladores/_fonte/auditorias/publicacao_dou3059_20261028_001/verificar.py
```

`stage-final.paths.z` contém exatamente os arquivos do envelope e o próprio envelope/lista. Os blocos normativos estão em `parte001-normas.paths.z` (1.500) e `parte002-normas.paths.z` (1.559); são disjuntos. Os demais caminhos são controles e provas. Para a publicação dividida, ROOT pode incluir controles uma única vez no primeiro bloco e somente as 1.559 normas no segundo. Os arquivos de configuração Git e o índice não foram alterados.

Preserve os espaços finais que representam quebras de linha Markdown e o EOF exato dos MDs. Não execute formatador, limpeza de espaços ou geradores sobre a seleção congelada. As dependências de replay e os dois fragmentos gzip de fontes primárias já estão nos mapas originais vinculados pelo envelope. Os replays e 23 testes substantivos foram repetidos pelo ROOT; este complemento confere seleção, SHA e cópias.

A proposta pública `cobertura-ROOT/` contém cópias byte a byte das provas privadas de reconciliação de 461.223 blobs no HEAD 457a424. `cobertura-copias.json` mantém os caminhos lógicos originais e a correspondência de SHA. Os recibos históricos não foram reescritos. O script e log ROOT são snapshots de evidência; seus caminhos originais permanecem literais. Essa prova não certifica integralidade normativa universal, vigência ou cobertura de alterações posteriores. Não contém atos municipais: eventuais índices municipais dos antecedentes servem somente à deduplicação e não à contagem de normas.

O envelope é o fechamento efetivo e inclui todos os arquivos deste complemento anteriores a ele. `manifesto-publicacao.json`, `publicacao.paths.*` e `mapa-publicacao.json` são camadas antecedentes preservadas; não use isoladamente suas listas para incluir o envelope final. Não há aplicação automática, alteração de canônicos ou operação Git neste pacote.
