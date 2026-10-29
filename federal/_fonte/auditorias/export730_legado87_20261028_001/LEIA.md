Export portátil para os 730 candidatos Normas 019

O pacote original permanece imutável. Seu recibo exige html2md SHA 6ad648a6a94c8d51d880a2d79c39f1abe751032d3355e468363e43ca83fdcdc6 e baixar_federal SHA 4889285109716ea3f7e753e8af2991b874d1f3b7265488756a98e0610c703495. Como o worktree tem edições diferentes, ambos foram recuperados do HEAD documentado e arquivados com exatamente os bytes esperados. Nenhum global foi sobrescrito ou atribuído a esta frente.

mapa_versoes.json liga cada um dos 16 caminhos lógicos declarados ao arquivo versionado de mesmo SHA. Dois auxiliares transitivos do HEAD são declarados separadamente, sem inventar hashes antecedentes. O módulo marked arquivado é byte a byte igual ao runtime observado, e o replay confere os resultados dos candidatos. O mapa lógico original é antecedente histórico; apenas mapa_efetivo730.json deve orientar a publicação deste complemento. O mapa efetivo exclui todos os caminhos globais em scripts/, inclusive os dois divergentes, e inclui as cópias versionadas.

replay730_export.py mantém os comparadores, fontes, candidatos e hashes originais. Só adapta caminhos/importações, verifica o mapeamento, usa as dependências arquivadas e proíbe HTTP. Reproduziu os 730 corpos integralmente em dois motores e HTML5, com identidade e fecho principal preservados. Os patches mostram a adaptação de IO. Originais e recibos foram copiados sem modificar seus SHAs.

promover730_export.py tem dry-run por padrão. --apply é exclusivo ROOT e não foi executado pelo agente. Valida o export, todos os insumos e o replay, confere ausência atual por caminho e número/ano no HEAD e só então pode criar backups, intenção e candidatos por ligação atômica sem sobrescrita. Os quatro métodos de proteção são idênticos por AST aos do promotor antecedente. O dry-run passou sem escrita.

Oito testes de limites, cinco de segurança e quatro de isolamento passaram. Os últimos comprovam importação das cópias arquivadas, rejeição de código sem mapeamento, rejeição de bytes divergentes e rejeição de symlink em insumo. Nenhum teste modificou snapshots anteriores ou canônicos.

O mapa efetivo é anterior à aplicação: inclui candidatos privados e dados completos, mas nenhum canônico ainda ausente. Após a aplicação ROOT, um controle separado deve acrescentar canônicos, backups, journal e logs conferidos. Não usar os geradores para sobrescrever este complemento congelado. Guard 87 continua arquivado; o novo cliente 021 usa explicitamente esses módulos para manter a alimentação independente dos globais em edição.
