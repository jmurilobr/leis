Export final portátil para promover os 730 candidatos

Usar replay730_export.py e promover730_export.py deste diretório. O promotor tem dry-run padrão; --apply continua exclusivo ROOT e não foi executado pelo agente. O replay e o dry-run final passaram no HEAD 437bce53bec67cc65c8a72727425d53ab9cb7fe3, com ausência por caminho e número/ano. Foram preservados todos os comparadores, fontes, candidatos e SHAs antecedentes.

O complemento 001 arquivou os 16 insumos exatamente exigidos pelo recibo original. html2md e baixar_federal foram recuperados do Git com os SHAs antigos; os globais em edição permanecem intocados. mapa_versoes.json, copiado sem alteração, resolve os caminhos lógicos para essas cópias. Nenhum SHA foi substituído pelo valor atual do worktree. Recibos e runners originais estão preservados como antecedente.

Este complemento 002 usa caminhos relativos ao repositório, inclusive para o módulo marked arquivado, e contém cópias locais de markdown-it-py, mdurl, html5lib, webencodings e six, com metadados/licenças. Os hashes de todos os arquivos dessas bibliotecas são verificados antes do replay. runtime.json registra as versões usadas agora, sem inventar uma pinagem antiga não registrada. Python e Node são requisitos de execução; não é necessário instalar bibliotecas Python nem acessar rede ou caches normativos para o replay.

Passaram 18 testes: oito de limites principal/incorporados, cinco de segurança e cinco de isolamento, incluindo bibliotecas locais. O primeiro ensaio do teste de isolamento teve um nome de variável incorreto no próprio teste; foi corrigido e todos os testes passaram em testes_final.log. Não houve alteração dos candidatos ou do predicado normativo.

O mapa efetivo de publicação é mapa_efetivo730.json deste diretório. Ele inclui os dados e candidatos congelados, o export 001 e este complemento; não inclui nenhum caminho global em scripts/. O mapa lógico original é prova histórica e não orienta staging dos globais divergentes. Após --apply ROOT, um controle separado acrescentará os canônicos, backups, journal e logs conferidos. Este mapa é anterior à aplicação e não inclui canônicos ainda ausentes.

Os patches permitem conferir a adaptação de IO/importações/proveniência. Os quatro métodos de proteção do promotor permanecem idênticos por AST ao original. Módulos de caminho lógico sem export declarado não recebem fallback silencioso para o global. Não reexecutar geradores sobre snapshots congelados. Nenhum global, canônico, registro, WORKLOG ou Git foi alterado pelo agente.
