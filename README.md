# Esteira de Reembolso — Demo CI/CD (GitHub Actions + Pages)

Demonstração mínima de **monitoramento, governança e melhoria contínua** para um app de
solicitação de reembolso, usando **GitHub Actions** com a esteira
**Dev → Homologação → Produção**, aprovação manual obrigatória em produção, secrets por
ambiente, dashboard DORA e alertas de falha.

> A página publicada é um "Olá mundo" que mostra o ambiente, a versão e o commit do deploy.

---

## Estrutura

```
esteira-reembolso/
├─ .github/workflows/deploy.yml   # esteira: QA → Dev → Homolog → [aprovação] → Prod → Pages
├─ src/
│  ├─ index.html                  # página "Olá mundo" (badge muda de cor por ambiente)
│  └─ dashboard.html              # dashboard DORA (lê metrics.json)
├─ scripts/
│  ├─ build.sh                    # injeta ambiente/versão/commit no HTML
│  └─ dora.py                     # calcula Deploy Frequency, Failure Rate, MTTR
└─ README.md
```

---

## Passo a passo (setup no GitHub)

1. **Crie o repositório** e faça o push deste conteúdo para a branch `main`.

2. **Habilite o Pages**
   `Settings ▸ Pages ▸ Build and deployment ▸ Source = GitHub Actions`.

3. **Crie os três ambientes**
   `Settings ▸ Environments ▸ New environment`, criando:
   `dev`, `homologacao`, `producao`.

4. **Aprovação manual em produção** (o gate obrigatório)
   No ambiente **`producao`**, marque **Required reviewers** e adicione o(s) aprovador(es).
   Só assim o job `deploy-prod` fica pausado aguardando aprovação humana.
   > Dica de governança: em ambiente regulado, use **segregação de funções** — quem
   > desenvolve não deve ser o mesmo que aprova produção.

5. **Secrets por ambiente** (isolamento de credenciais)
   Em cada ambiente, `Environment secrets ▸ Add secret`:
   - `APP_BASE_URL` — valor **diferente** por ambiente (dev/homolog/prod).
   - `SLACK_WEBHOOK_URL` — *(opcional)* webhook para os alertas. Sem ele, a falha
     abre automaticamente uma **Issue** de incidente.

6. **Rode a esteira**
   Faça um push em `main` (ou `Actions ▸ Run workflow`). A esteira executa Dev e
   Homologação automaticamente e **para em Produção** aguardando sua aprovação.
   Após aprovar, o site vai ao ar em `https://<usuario>.github.io/<repo>/`.

---

## O que cada requisito atende

| Requisito | Onde está |
|---|---|
| Versionamento em Git | o próprio repositório |
| Pipeline com stages | `deploy.yml`: jobs `qa → deploy-dev → deploy-homolog → deploy-prod → publish-pages` |
| Aprovação manual em Prod | `Required reviewers` no ambiente `producao` |
| Secrets por ambiente | Environment secrets (`APP_BASE_URL` por ambiente) |
| Dashboard (Deploy Freq, Failure Rate, MTTR) | `dashboard.html` + `metrics.json` (gerado por `dora.py`) |
| Alertas de falha | job `notify-failure` (Slack ou Issue) |
| Revisão de incidentes | Issues rotuladas `incidente,deploy` viram a pauta da reunião de revisão |

---

## Métricas (DORA)

Na etapa de produção, a esteira consulta a API do GitHub (runs da própria `deploy.yml`),
calcula as métricas com `scripts/dora.py` e grava `metrics.json` junto do site. O
`dashboard.html` lê esse arquivo e classifica cada métrica (Elite/Alto/Médio/Baixo):

- **Deploy Frequency** — deploys de produção bem-sucedidos por semana.
- **Change Failure Rate** — % de execuções concluídas que falharam.
- **MTTR** — tempo médio entre uma falha e o próximo sucesso.
- **Lead Time** *(aprox.)* — duração média de um deploy bem-sucedido.

Antes do primeiro deploy, o dashboard mostra **dados de exemplo** e avisa isso.

---

## Mapeamento para o cenário real (Power Platform)

Nesta demo, o Pages hospeda **um** site, então Dev e Homologação atuam como **gates de
promoção** (com artefatos baixáveis), e só Produção publica ao vivo. Num app **Low Code**
de verdade, cada ambiente é um **ambiente separado** e a esteira exporta/importa a solução:

| Demo (GitHub Pages) | Produção real (Power Platform) |
|---|---|
| `src/index.html` | Solução (app + flows + tabelas) exportada como *managed/unmanaged* |
| `build.sh` | `Export Solution` → `unpack` → commit no Git |
| Deploy Dev/Homolog/Prod | `Import Solution` em cada ambiente via Power Platform Build Tools |
| Aprovação em `producao` | *Approval* + change management (segregação de funções) |
| Secrets por ambiente | Connection references / Environment variables por ambiente |
| DORA + Issues | Power Platform / App Insights analytics + registro de incidentes |

---

## Rodar localmente

```bash
bash scripts/build.sh dev "Desenvolvimento" dist
python3 -m http.server -d dist 8080   # abra http://localhost:8080
```

Abrir `src/index.html` direto no navegador também funciona — sem os placeholders
substituídos, a página assume o modo "local".
