# Farm Distribuída P2P com Balanceamento de Carga Dinâmico

Proposta de arquitetura e implementação de uma *farm* de processamento distribuído heterogênea com protocolo de empréstimo bilateral de trabalhadores (*workers*), balanceamento dinâmico de carga e tolerância a falhas.

---

## 📌 Informações Acadêmicas

* **Instituição:** CEUB - Centro Universitário de Brasília
* **Disciplina:** Arquitetura de Sistemas Distribuídos (2026/2)
* **Professor:** Prof. Michel Junio Ferreira Rosa

---

## 📅 Cronograma Oficial e Entregas das Sprints

O desenvolvimento do projeto é cumulativo e estruturado em quatro Sprints principais ao longo do semestre de 2026/2:

| Etapa | Janela / Duração | Data de Entrega | Resultado Obrigatório & Escopo |
| :--- | :---: | :---: | :--- |
| **Sprint 1: Base de Comunicação** | 3 semanas (21 dias) | **01/10/2026** | Comunicação por sockets TCP, enquadramento NDJSON, envelope padrão de mensagens, controle de sessão, registro e monitoramento (*heartbeat*). |
| **Sprint 2: Farm Autônoma Completa** | 3 semanas (21 dias) | **22/10/2026** | Submissão e processamento de tarefas, tratamento de falhas, retentativas idempotentes, medição de fila, detecção de saturação e envio de métricas. |
| **Sprint 3: Sistema Completo Interno** | 4 semanas (28 dias) | **19/11/2026** | Protocolo completo de empréstimo bilateral entre *masters* da própria equipe, controle de época (*assignment_epoch*), redirecionamento e retorno comprovado. |
| **Sprint 4: Integração Inter-Grupos** | 2 semanas (14 dias) | **03/12/2026** | Interoperabilidade e testes cruzados entre implementações de equipes independentes usando o contrato comum[cite: 1]. |
| **Apresentação Final** | - | **03/12/2026** | Demonstração prática do ambiente integrado com transmissão de carga e métricas em tempo real. |

---

## 🎯 Visão Geral do Projeto

O objetivo do projeto é construir uma solução de computação distribuída em *farm* sem um orquestrador central único. Cada equipe opera uma instância composta por um nó coordenador (*Master*), executores (*Workers*), um submissor de carga (*Client*) e um receptor de métricas (*Collector*).

Quando a fila de tarefas de um *Master* entra em estado de saturação, ele atua como solicitante e negocia o empréstimo temporário de capacidade ociosa de *Masters* vizinhos através de um protocolo bilateral.

---

## 🏗️ Arquitetura de Processos e Papéis

O sistema é formado por cinco tipos de processos independentes que se comunicam exclusivamente via conexões TCP bidirecionais:

1. **Master (Coordenador):**
   * Administra a fila local de tarefas e gerencia o ciclo de vida dos *workers*.
   * Monitora os limiares de saturação e liberação da farm.
   * Atua como servidor para *workers* e clientes, e como cliente/par ao negociar com outros *masters*.
   * Garante que nenhuma tarefa seja processada ou contabilizada em duplicidade.

2. **Worker (Executor):**
   * Processa tarefas distribuídas pelo *Master* atual (executa uma tarefa por vez).
   * Mantém um canal ativo de controle e envio periódico de *heartbeat*[cite: 1].
   * Troca de *Master* temporariamente apenas quando redirecionado via protocolo de empréstimo.

3. **Client (Gerador de Carga):**
   * Submete tarefas com parâmetros configuráveis e sementes reprodutíveis diretamente ao *Master*

4. **Collector (Servidor de Telemetria):**
   * Processo passivo que recebe e armazena relatórios de desempenho e métricas enviadas pelo *Master*.

5. **Master Par / Vizinho (Peer):**
   * Instância externa de *Master* utilizada na Sprint 3 (da própria equipe) e na Sprint 4 (de outra equipe) para negociação bilateral de capacidade.

---

## ⚙️ Diretrizes e Restrições Técnicas

* **Comunicação Nativa:** Uso exclusivo de sockets TCP nativos da linguagem/sistema operacional. Proibida a utilização de frameworks ou abstrações como REST/HTTP, gRPC, WebSockets, Socket.IO, ZeroMQ, brokers de mensagem, RPC pronto ou programação assíncrona (`asyncio`).
* **Concorrência Nativa:** Gerenciamento por processos e threads independentes com primitivas nativas de sincronização (*locks*, semáforos, eventos e filas protegidas em memória).
* **Enquadramento de Mensagens:** Formato NDJSON (*Newline Delimited JSON* - UTF-8 finalizado por quebra de linha `\n`), com tamanho máximo de 64 KB por mensagem.
* **Convenção de Nomes:** Padronização estrita em `lower_snake_case` para todas as chaves, comandos, tipos de mensagens e identificadores.
* **Garantia de Identidade e Sessão:** Identificação por UUIDs v4 e rótulos legíveis. Controle de sessão via época (*assignment_epoch*) para rejeitar comandos ou resultados atrasados/obsoletos.

---

## 🔄 Fluxo de Negociação e Empréstimo Bilateral

A cooperação entre *masters* para balanceamento de carga segue um ciclo de 7 etapas obrigatórias:

1. **Solicitação de Ajuda:** O *master* saturado envia um pedido de capacidade ao *master* vizinho.
2. **Oferta e Reserva:** Se possuir capacidade ociosa e preservar sua cota mínima local, o *master* cedente reserva atômica e temporariamente um *worker* e envia uma oferta.
3. **Confirmação e Persistência:** O solicitante confirma a aceitação. O cedente registra o empréstimo em histórico persistente e incrementa a época de sessão.
4. **Redirecionamento:** O cedente instrui o *worker* a encerrar a conexão atual e se conectar ao *master* receptor.
5. **Operação Temporária:** O *worker* se registra no receptor, executa tarefas e devolve resultados usando o mesmo contrato de execução local.
6. **Liberação de Carga:** Quando a fila do receptor normaliza, o envio de tarefas ao *worker* emprestado é interrompido e um comando de liberação é enviado.
7. **Retorno Comprovado:** O *worker* reconecta à sua origem. O *master* de origem confirma o retorno, grava o fechamento do empréstimo, atualiza a época de sessão e notifica o receptor.

---

## 📊 Telemetria e Monitoramento de Desempenho

A cada 10 segundos, o processo *Master* envia relatórios periódicos de telemetria ao seu *Collector*. As métricas acompanhadas incluem:

* **Contadores de Fila e Tarefas:** Quantidade de tarefas pendentes, em execução, concluídas com sucesso e falhas terminais.
* **Estado dos Workers:** Distribuição dos *workers* entre ativos, ocupados, ociosos, reservados para empréstimo, cedidos a terceiros, recebidos de outros *masters* e indisponíveis.
* **Indicadores de Saturação:** Monitoramento contínuo com critérios de histerese para evitar oscilações na solicitação ou devolução de recursos.

---

## 🧪 Estratégia de Testes de Aceitação

A validação da aplicação é realizada por meio de testes de aceitação que simulam cenários normais e de falha[cite: 1]:

* **Comunicação:** Validação de fragmentação TCP, múltiplas mensagens em um mesmo buffer e tratamento de JSONs malformados sem interrupção dos serviços.
* **Resiliência e Reconexão:** Simulação de quedas de conexão, tratamento de *timeouts*, reconexão de *workers* e prevenção de cadastros duplicados.
* **Idempotência e Tolerância a Falhas:** Garantia de contabilização única de tarefas mesmo em casos de perda de confirmação (*ACK*), entrega duplicada de resultados ou mensagens obsoletas.
* **Integração e Interoperabilidade:** Teste de troca de *workers* entre *masters* com concorrência de pedidos, expiração de reservas e falhas parciais de rede.
