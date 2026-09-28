# Política de Governança e LGPD — AIReport Gen-Experience

**Versão:** 1.0 (Sprint 4)  
**Escopo:** Enterprise Challenge FIAP × Dasa/Genera — aplicação de demonstração  
**Base legal:** Lei nº 13.709/2018 (LGPD), arts. 8º e 11 (dados genéticos = dado sensível)

---

## 1. Finalidade

O AIReport Gen-Experience trata dados genéticos **somente para** explicar o
próprio relatório do titular (linguagem simples, riscos, prevenção). Não há
classificação de crédito, seleção, compartilhamento comercial ou decisão
automatizada com efeitos jurídicos.

## 2. Inventário de dados

Fonte de verdade em código: `app/governance/policy.py` (`DATA_INVENTORY`).

| Dado | Onde fica | Retenção | Base legal |
|------|-----------|----------|------------|
| Relatório genético (PDF) | `data/raw/` — **fora do git** desde a Etapa 1 | Enquanto o titular mantiver o arquivo | Consentimento |
| Índice vetorial | `data/vectordb/` — fora do git | Regenerável; apagado no reprocessamento | Consentimento |
| Logs operacionais | `logs/app.log` — fora do git | 30 dias (`LOG_RETENTION_DAYS`) | Legítimo interesse (operação) |
| Eventos de auditoria | `logs/audit.log` — fora do git | 30 dias (`LOG_RETENTION_DAYS`) | Legítimo interesse (governança) |
| Consentimento | `data/consent.json` — fora do git | Até revogação | Art. 8º (registro) |
| Histórico de conversa | Memória do processo (**volátil**) | Reinício/reprocessamento | Consentimento |
| Pergunta/resposta ao LLM | API externa Groq (operador) | Conforme política da Groq | Consentimento |

## 3. Consentimento do titular (art. 8º)

- `GET  /api/v1/consent` — retorna `{required, granted, policy_version, current_policy_version, granted_at}`.
- `POST /api/v1/consent` — registra (`granted: true`) ou **revoga** (`granted: false`).
- Registro guarda **apenas**: flag, versão da política, timestamp e origem —
  inventário fechado de chaves (`app/governance/consent.py`), sem PII.
- Com `REQUIRE_CONSENT=true`, o `POST /api/v1/chat` retorna **403** até o
  consentimento ser registrado (padrão: `false`, para não quebrar a demo).
- Toda alteração gera evento `consent_update` em `logs/audit.log`.
- A tela de consentimento no app móvel será exibida na Etapa 7 (React Native).

## 4. Minimização e proteção desde o design

1. **Logs nunca recebem conteúdo do usuário** — guard ativo em
   `app/observability/audit.py` (`FORBIDDEN_FIELDS` → `ValueError`), coberto
   por teste automatizado.
2. Logs registram apenas metadados: tamanhos, contagens, modelo, latência,
   status, `trace_id`.
3. Caminhos de arquivo viram `sha256:xxxxxxxxxxxx` no log de auditoria.
4. PDF com PII está fora do versionamento (Etapa 1: `git rm --cached` +
   `data/raw/*.pdf` no `.gitignore`).
5. Segredos (`.env`) fora do git; `.env.example` sem chave real.
6. Helper `mask_name()` disponível para anonimização em qualquer saída futura.

## 5. Retenção e expurgo

- `LOG_RETENTION_DAYS` (padrão **30 dias**) controla a remoção de `*.log`.
- Expurgo executado **na inicialização da API** (antes de abrir os handlers)
  e manualmente:

  ```bash
  py -3.10 -m app.governance.policy
  ```

- Arquivos em uso (Windows) são ignorados com segurança — nunca bloqueiam a
  operação (`purge_expired_logs`).
- Dados voláteis (conversa) morrem com o processo; não há banco de dados de
  pacientes nesta etapa.

## 6. Logs e auditoria (rastreabilidade)

- `logs/app.log` — eventos `http_request` (método, rota, status, latência, `trace_id`).
- `logs/audit.log` — eventos `chat_turn`, `report_access`, `reprocess`, `consent_update`.
- `X-Trace-ID` correlaciona requisição, resposta e eventos internos.
- Retenção dos logs = item 5.

## 7. Transferência a operador (LLM)

Durante a geração, trechos do relatório são enviados à API da **Groq**
(operador, EUA). Em produção isso exige: DPA/cláusulas contractuais,
aviso ao titular e avaliação de transferência internacional (LGPD, art. 33).
Nesta etapa acadêmica, o uso é declarado aqui e o titular é informado na UI
(disclaimers).

## 8. Direitos do titular (art. 18)

Como exercer nesta aplicação:

| Direito | Como |
|---------|------|
| Acesso | O próprio app mostra o relatório (`/api/v1/report`) |
| Eliminação | Apagar `data/raw/*.pdf`, `data/consent.json`, `logs/*.log` e reiniciar o servidor (conversa é volátil) |
| Revogação | `POST /api/v1/consent {"granted": false}` |
| Informação | Este documento + README |

## 9. Purga do histórico Git — **PENDENTE (não executada nesta etapa)**

O arquivo com PII saiu do versionamento (Etapa 1), **mas ainda existe no
histórico** dos commits já publicados. A purga do histórico **não foi
executada** (decisão consciente — exige coordenação com força-push). Procedimento
recomendado antes da entrega final:

```bash
# 1) instalar git-filter-repo (uma vez)
pip install git-filter-repo

# 2) executar no clone limpo (backup antes!)
cp -r <repo> <repo>-backup
cd <repo>
git filter-repo --path data/raw/genetic_report.pdf --invert-paths

# 3) publicar a história reescrita
git remote add origin https://github.com/ReMendess/genreport-ai_Sprint3.git
git push --force origin main

# 4) avisar colaboradores para re-clonar (histórico divergente)
```

> ⚠️ Após a purga, **todos** os clones existentes devem ser recriados.
> Executar somente com backup e janela de coordenação com a equipe.

## 10. Riscos conhecidos e status

| Risco | Mitigação | Status |
|-------|-----------|--------|
| PII no histórico git | Untrack feito; purga documentada (item 9) | ⏳ Pendente |
| Conteúdo em logs | Guard `FORBIDDEN_FIELDS` + teste automatizado | ✅ Feito |
| Consentimento ausente | Endpoint + gate opcional (item 3) | ✅ Feito |
| Logs crescem sem limite | Retenção + expurgo (item 5) | ✅ Feito |
| Dado sensível ao LLM externo | Declaração item 7; DPA exigido em produção | ⏳ Produção |
| Sem HTTPS/auth | Etapa de Deploy (escopo posterior) | ⏳ Futuro |

## 11. Responsáveis e revisão

- Responsável: Renan de Oliveira Mendes (RM563145) — Enterprise Challenge FIAP.
- Revisão prevista: Etapa 9 (README final + evidências da Sprint 4).
- Próxima versão: 1.1 ao concluir avaliação de modelo (Etapa 5) e app móvel (Etapa 7).

---

*Documento vivo: alterações de política devem incrementar a versão acima e
registrar novo consentimento quando o `current_policy_version` mudar.*
