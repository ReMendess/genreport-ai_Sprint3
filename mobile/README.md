# AIReport Gen-Experience — App (React Native / Expo)

Aplicação móvel da Sprint 4 (Etapa 7) consumindo a API REST do projeto.

## Requisitos

- Node.js 18+ (validado com Node 22)
- API acessivel na rede (obrigatorio para celular fisico):
  `python -m uvicorn api.main:app --host 0.0.0.0 --port 8010`
- Porta 8010 liberada no firewall do PC (uma vez, PowerShell **como admin**):
  `New-NetFirewallRule -DisplayName "AIReport API 8010" -Direction Inbound -LocalPort 8010 -Protocol TCP -Action Allow`
- Expo Go no celular **ou** emulador Android
- Celular e PC na **mesma rede Wi-Fi**

## Instalação e execução

```bash
cd mobile
npm install
npm start            # abre o Metro Bundler
# ou:
npm run android      # emulador Android
npm run typecheck    # checagem estrita de tipos (tsc --noEmit)
npm run bundle:android  # bundle de produção (validação sem emulador)
```

## Configurando o endereço da API

`src/config.ts` resolve o endereco automaticamente, nesta ordem:

| Prioridade | Origem | Quando usar |
|---|---|---|
| 1 | `EXPO_PUBLIC_BASE_URL` | Voce quer forcar um endereco |
| 2 | **Auto-deteccao do Metro** (`expo-constants`) | Celular via Expo Go — pega o IP do PC sozinho |
| 3 | `http://10.0.2.2:8010` (Android) / `http://localhost:8010` | Emulador / web |

**Celular (Expo Go):** nao precisa configurar nada — o app descobre o IP do PC
no host do Metro. Somente garanta que a API esta em `0.0.0.0` e a porta liberada.

**Forcar um endereco especifico (opcional):**

```bash
# Windows (PowerShell)
$env:EXPO_PUBLIC_BASE_URL="http://192.168.15.16:8010"; npm start
# Linux/macOS
EXPO_PUBLIC_BASE_URL=http://192.168.0.10:8010 npm start
```

**Teste rapido do endereco** (no navegador do proprio celular):
`http://<IP-do-PC>:8010/api/v1/health` deve responder `{"status":"ok"}`.
Se nao responder: a API nao esta em `0.0.0.0` ou o firewall esta bloqueando.

> Erro "Falha de conexao com a API (...)" = endereco errado, API nao acessivel
> na rede ou firewall fechado. Emulador Android usa `10.0.2.2`, nunca `localhost`.

## Fluxo do app

1. **Consentimento (LGPD)** — primeira execução mostra a tela de consentimento;
   registra via `POST /api/v1/consent` e persiste localmente (AsyncStorage).
2. **Painel** — `GET /api/v1/report` (resumo, risk cards, ancestralidade) +
   `GET /api/v1/status` (banner de índice degradado + botão de reprocessar via
   `POST /api/v1/reprocess`).
3. **Chat** — `POST /api/v1/chat` com exibição de fontes, badge de recusa
   (`refused`/`refusal_reason`) e percentual de fundamentação (`groundedness`).
4. **Status** — `/status` + `/metrics` (operação: uptime, latências, recusas).

## Expo Web (Etapa 8)

```bash
npm install       # já inclui react-dom + react-native-web
npm run web       # http://localhost:1921
npm run bundle:web
```

A API libera CORS via `CORS_ALLOW_ORIGINS` (padrão `*`; em produção use
uma lista explícita, ex.: `http://localhost:1921`). Preflight `OPTIONS`
tratado pelo middleware da FastAPI.

O chip **API conectada / API offline** no cabeçalho do Chat reflete o
estado de conexão (`apiOnline` do `AppContext`).

## Validação executada nesta etapa


- `npm run typecheck` (TypeScript estrito)
- `npm run bundle:android` (Metro + Babel, sem emulador)
- `npm run bundle:web` (bundle web + caminho de CORS)
- API local: fluxo E2E completo (consent → report → chat → reprocess → ops)
- Preflight `OPTIONS` + `Access-Control-Allow-Origin` validados contra a API
- Conexao em rede (Sprint 4, corrigido): auto-deteccao do IP do PC no Expo Go;
  API validada em `0.0.0.0` e acesso pelo IP da LAN

## Estrutura

```text
mobile/
├── App.tsx                # gate de consentimento + abas
├── index.ts               # registro do root component
├── env.d.ts               # tipagem mínima de EXPO_PUBLIC_*
├── src/
│   ├── config.ts          # BASE_URL por plataforma
│   ├── types.ts           # contratos JSON da API
│   ├── theme.ts           # identidade visual Dasa
│   ├── services/api.ts    # cliente HTTP (fetch + timeout + ApiError)
│   ├── context/AppContext.tsx  # consentimento + status global
│   ├── components/        # Banner, RiskCard
│   └── screens/           # Consent, Dashboard, Chat, Status
└── package.json
```

Os ícones das abas são emojis (sem dependências extras de ícones).
