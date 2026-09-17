# Farm Distribuída P2P com Balanceamento de Carga Dinâmico

Proposta de arquitetura e implementação de uma *farm* de processamento distribuído heterogênea com protocolo de empréstimo bilateral de trabalhadores (*workers*), balanceamento dinâmico de carga e tolerância a falhas.

---

## 📌 Informações Acadêmicas

* **Instituição:** CEUB - Centro Universitário de Brasília
* **Disciplina:** Arquitetura de Sistemas Distribuídos (2026/2)
* **Professor:** Prof. Michel Junio Ferreira Rosa
* **Protocolo:** `sd_2026_2_v1`

---

## 📅 Cronograma Oficial e Entregas das Sprints

O desenvolvimento do projeto é cumulativo e estruturado em quatro Sprints principais ao longo do semestre de 2026/2[cite: 1]:

| Etapa | Janela / Duração | Data de Entrega | Resultado Obrigatório & Escopo |
| :--- | :---: | :---: | :--- |
| **Sprint 1: Base de Comunicação** | 3 semanas (21 dias) | **01/10/2026** | Comunicação por sockets TCP, enquadramento NDJSON, envelope padrão de mensagens, controle de sessão, registro e monitoramento (*heartbeat*)[cite: 1]. |
| **Sprint 2: Farm Autônoma Completa** | 3 semanas (21 dias) | **22/10/2026** | Submissão e processamento de tarefas, tratamento de falhas, retentativas idempotentes, medição de fila, detecção de saturação e envio de métricas[cite: 1]. |
| **Sprint 3: Sistema Completo Interno** | 4 semanas (28 dias) | **19/11/2026** | Protocolo completo de empréstimo bilateral entre *masters* da própria equipe, controle de época (*assignment_epoch*), redirecionamento e retorno comprovado[cite: 1]. |
| **Sprint 4: Integração Inter-Grupos** | 2 semanas (14 dias) | **03/12/2026** | Interoperabilidade e testes cruzados entre implementações de equipes independentes usando o contrato comum[cite: 1]. |
| **Apresentação Final** | - | **03/12/2026** | Demonstração prática do ambiente integrado com transmissão de carga e métricas em tempo real[cite: 1]. |
| **Prova Regimental** | 1 semana após apr. | **10/12/2026** | Avaliação individual conforme planejamento docente[cite: 1]. |

---

## 🎯 Visão Geral do Projeto

O objetivo do projeto é construir uma solução de computação distribuída em *farm* sem um orquestrador central único[cite: 1]. Cada equipe opera uma instância composta por um nó coordenador (*Master*), executores (*Workers*), um submissor de carga (*Client*) e um receptor de métricas (*Collector*)[cite: 1].

Quando a fila de tarefas de um *Master* entra em estado de saturação, ele atua como solicitante e negocia o empréstimo temporário de capacidade ociosa de *Masters* vizinhos através de um protocolo bilateral[cite: 1].

---

## 🏗️ Arquitetura de Processos e Papéis

O sistema é formado por cinco tipos de processos independentes que se comunicam exclusivamente via conexões TCP bidirecionais[cite: 1]:

1. **Master (Coordenador):**
   * Administra a fila local de tarefas e gerencia o ciclo de vida dos *workers*[cite: 1].
   * Monitora os limiares de saturação e liberação da farm[cite: 1].
   * Atua como servidor para *workers* e clientes, e como cliente/par ao negociar com outros *masters*[cite: 1].
   * Garante que nenhuma tarefa seja processada ou contabilizada em duplicidade[cite: 1].

2. **Worker (Executor):**
   * Processa tarefas distribuídas pelo *Master* atual (executa uma tarefa por vez)[cite: 1].
   * Mantém um canal ativo de controle e envio periódico de *heartbeat*[cite: 1].
   * Troca de *Master* temporariamente apenas quando redirecionado via protocolo de empréstimo[cite: 1].

3. **Client (Gerador de Carga):**
   * Submete tarefas com parâmetros configuráveis e sementes reprodutíveis diretamente ao *Master*[cite: 1].

4. **Collector (Servidor de Telemetria):**
   * Processo passivo que recebe e armazena relatórios de desempenho e métricas enviadas pelo *Master*[cite: 1].

5. **Master Par / Vizinho (Peer):**
   * Instância externa de *Master* utilizada na Sprint 3 (da própria equipe) e na Sprint 4 (de outra equipe) para negociação bilateral de capacidade[cite: 1].

---

## ⚙️ Diretrizes e Restrições Técnicas

* **Comunicação Nativa:** Uso exclusivo de sockets TCP nativos da linguagem/sistema operacional. Proibida a utilização de frameworks ou abstrações como REST/HTTP, gRPC, WebSockets, Socket.IO, ZeroMQ, brokers de mensagem, RPC pronto ou programação assíncrona (`asyncio`)[cite: 1].
* **Concorrência Nativa:** Gerenciamento por processos e threads independentes com primitivas nativas de sincronização (*locks*, semáforos, eventos e filas protegidas em memória)[cite: 1].
* **Enquadramento de Mensagens:** Formato NDJSON (*Newline Delimited JSON* - UTF-8 finalizado por quebra de linha `\n`), com tamanho máximo de 64 KB por mensagem[cite: 1].
* **Convenção de Nomes:** Padronização estrita em `lower_snake_case` para todas as chaves, comandos, tipos de mensagens e identificadores[cite: 1].
* **Garantia de Identidade e Sessão:** Identificação por UUIDs v4 e rótulos legíveis. Controle de sessão via época (*assignment_epoch*) para rejeitar comandos ou resultados atrasados/obsoletos[cite: 1].

---

## 🔄 Fluxo de Negociação e Empréstimo Bilateral

A cooperação entre *masters* para balanceamento de carga segue um ciclo de 7 etapas obrigatórias[cite: 1]:

1. **Solicitação de Ajuda:** O *master* saturado envia um pedido de capacidade ao *master* vizinho[cite: 1].
2. **Oferta e Reserva:** Se possuir capacidade ociosa e preservar sua cota mínima local, o *master* cedente reserva atômica e temporariamente um *worker* e envia uma oferta[cite: 1].
3. **Confirmação e Persistência:** O solicitante confirma a aceitação. O cedente registra o empréstimo em histórico persistente e incrementa a época de sessão[cite: 1].
4. **Redirecionamento:** O cedente instrui o *worker* a encerrar a conexão atual e se conectar ao *master* receptor[cite: 1].
5. **Operação Temporária:** O *worker* se registra no receptor, executa tarefas e devolve resultados usando o mesmo contrato de execução local[cite: 1].
6. **Liberação de Carga:** Quando a fila do receptor normaliza, o envio de tarefas ao *worker* emprestado é interrompido e um comando de liberação é enviado[cite: 1].
7. **Retorno Comprovado:** O *worker* reconecta à sua origem. O *master* de origem confirma o retorno, grava o fechamento do empréstimo, atualiza a época de sessão e notifica o receptor[cite: 1].

---

## 📊 Telemetria e Monitoramento de Desempenho

A cada 10 segundos, o processo *Master* envia relatórios periódicos de telemetria ao seu *Collector*[cite: 1]. As métricas acompanhadas incluem[cite: 1]:

* **Contadores de Fila e Tarefas:** Quantidade de tarefas pendentes, em execução, concluídas com sucesso e falhas terminais[cite: 1].
* **Estado dos Workers:** Distribuição dos *workers* entre ativos, ocupados, ociosos, reservados para empréstimo, cedidos a terceiros, recebidos de outros *masters* e indisponíveis[cite: 1].
* **Indicadores de Saturação:** Monitoramento contínuo com critérios de histerese para evitar oscilações na solicitação ou devolução de recursos[cite: 1].

---

## 🧪 Estratégia de Testes de Aceitação

A validação da aplicação é realizada por meio de testes de aceitação que simulam cenários normais e de falha[cite: 1]:

* **Comunicação:** Validação de fragmentação TCP, múltiplas mensagens em um mesmo buffer e tratamento de JSONs malformados sem interrupção dos serviços[cite: 1].
* **Resiliência e Reconexão:** Simulação de quedas de conexão, tratamento de *timeouts*, reconexão de *workers* e prevenção de cadastros duplicados[cite: 1].
* **Idempotência e Tolerância a Falhas:** Garantia de contabilização única de tarefas mesmo em casos de perda de confirmação (*ACK*), entrega duplicada de resultados ou mensagens obsoletas[cite: 1].
* **Integração e Interoperabilidade:** Teste de troca de *workers* entre *masters* com concorrência de pedidos, expiração de reservas e falhas parciais de rede[cite: 1].
