# ATIVIDADE PRÁTICA 01: Enquadramento NDJSON e Handshake de Registro

**Instituição:** CEUB / FATECS - Tecnologia da Informação (Campus Taguatinga)  
**Curso:** Ciência da Computação (Turma UN, Matutino)  
**Disciplina:** Arquitetura de Sistemas Distribuídos  
**Professor:** Michel Junio Ferreira Rosa  
**Formato:** Atividade em laboratório, nos grupos do projeto  
 
---

## Contexto e Objetivo

Esta é a atividade inicial do projeto P2P com Balanceamento de Carga Dinâmico e serve de preparação direta para a Sprint 1. O objetivo é que cada grupo saia do laboratório com um canal TCP confiável entre dois processos distintos, falando um protocolo de mensagens em JSON por linha, com identidade persistente. É o alicerce exigido pela Sprint 1, construído em escala reduzida para que os erros apareçam agora, e não na véspera.

---

## Roteiro

1. **Estrutura Base:** Partindo do material *Exemplo Socket* disponível na sala, separar o código em dois executáveis, `master.py` e `worker.py`, cada um com arquivo de configuração próprio (`config.json`) contendo UUID gerado na primeira execução e persistido, além de label, host e port.
2. **Enquadramento NDJSON:** Implementar `send_msg` e `recv_msgs` com enquadramento NDJSON: cada mensagem é um JSON serializado em uma linha, terminada por quebra de linha, e o receptor mantém um buffer que acumula bytes parciais e só entrega linhas completas.
3. **Validação de Envelope:** Definir e validar o envelope mínimo: `type`, `msg_id`, `request_id`, `origin` (UUID e label), `timestamp` e `payload`. Mensagem sem campo obrigatório ou com JSON inválido deve ser descartada com registro em log, nunca derrubar o processo.
4. **Registro e Tabela:** Implementar o par `register_worker` e `registration_ack`, com o master mantendo tabela de workers em memória indexada por UUID. Reconexão do mesmo UUID atualiza o registro, não cria duplicata.
5. **Formato de Logs:** Registrar logs em uma linha por evento, no formato:
   `grupo | origem | destino | type | request_id | resultado`

---

## Testes a Executar no Laboratório

Cada grupo deve demonstrar os cinco cenários abaixo em execução, com os logs à vista:

* **Fragmentação:** enviar um JSON grande em dois `send` e confirmar que chega inteiro.
* **Coalescência:** enviar três mensagens em rajada e confirmar que o receptor entrega três, não uma.
* **JSON Inválido:** enviar conteúdo malformado e confirmar que o processo sobrevive.
* **Identidade Duplicada:** subir dois workers com o mesmo UUID e descrever o comportamento escolhido.
* **Reconexão:** encerrar um worker, subir novamente e mostrar que a tabela do master permanece com um único registro.

---

## Resultado Esperado ao Final da Aula

Um master e pelo menos um worker executando como processos independentes, identificáveis pelo label nos logs, trocando mensagens enquadradas corretamente mesmo sob fragmentação e rajada, com registro reconhecido pelo master e reconexão sem duplicar o cadastro.
