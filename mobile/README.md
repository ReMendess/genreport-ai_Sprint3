# AIReport Gen-Experience — App (React Native / Expo)

Aplicação móvel da Sprint 4 (Etapa 7) consumindo a API REST do projeto.

## Requisitos

- Node.js 18+ (validado com Node 22)
- API rodando localmente (`python -m uvicorn api.main:app --port 8010`)
- Expo Go no celular **ou** emulador Android

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

O padrão é resolvido em `src/config.ts`:

| Ambiente | Padrão |
|---|---|
| Emulador Android | `http://10.0.2.2:8010` |
| iOS / Expo Web | `http://localhost:8010` |
| Expo Go (celular) | defina `EXPO_PUBLIC_BASE_URL` |

Exemplo (IP da sua máquina na LAN):

```bash
EXPO_PUBLIC_BASE_URL=http://192.168.0.10:8010 npm start
```

> Android (aplicativo real / arquiteturas novas): use o IP da LAN, não 10.0.2.2.

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
