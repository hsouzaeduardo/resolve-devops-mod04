#!/usr/bin/env python3
"""
Calcula métricas DORA a partir dos runs do workflow de deploy e grava metrics.json.

Espera receber, via stdin, o JSON de:
  gh api "/repos/$REPO/actions/workflows/deploy.yml/runs?per_page=100"

Uso (no workflow):
  gh api ".../runs?per_page=100" | python scripts/dora.py <dias> > dist/metrics.json

Métricas:
  - deploy_frequency_per_week : deploys de produção bem-sucedidos por semana
  - change_failure_rate       : falhas / total de execuções concluídas
  - mttr_hours                : tempo médio entre uma falha e o próximo sucesso
  - lead_time_hours           : duração média de um run bem-sucedido (aproximação)
  - daily                     : contagem ok/falha por dia (para o gráfico)
"""
import json
import sys
from datetime import datetime, timezone, timedelta

WINDOW_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 14


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    payload = json.load(sys.stdin)
    runs = payload.get("workflow_runs", [])

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=WINDOW_DAYS)

    # Considera apenas execuções concluídas dentro da janela.
    done = [
        r for r in runs
        if r.get("status") == "completed" and parse(r["created_at"]) >= since
    ]
    done.sort(key=lambda r: parse(r["created_at"]))

    success = [r for r in done if r.get("conclusion") == "success"]
    failure = [r for r in done if r.get("conclusion") == "failure"]

    total = len(success) + len(failure)
    weeks = max(WINDOW_DAYS / 7.0, 1e-9)

    deploy_freq = len(success) / weeks
    cfr = (len(failure) / total) if total else 0.0

    # MTTR: para cada falha, tempo até o próximo sucesso.
    recoveries = []
    for f in failure:
        f_time = parse(f["created_at"])
        nxt = next((parse(s["created_at"]) for s in success
                    if parse(s["created_at"]) > f_time), None)
        if nxt:
            recoveries.append((nxt - f_time).total_seconds() / 3600.0)
    mttr = sum(recoveries) / len(recoveries) if recoveries else 0.0

    # Lead time (aprox.): duração média dos runs de sucesso.
    durations = []
    for s in success:
        try:
            durations.append(
                (parse(s["updated_at"]) - parse(s["created_at"])).total_seconds() / 3600.0
            )
        except Exception:
            pass
    lead = sum(durations) / len(durations) if durations else 0.0

    # Série diária.
    daily = {}
    for r in done:
        day = parse(r["created_at"]).strftime("%d/%m")
        d = daily.setdefault(day, {"d": day, "ok": 0, "fail": 0})
        if r.get("conclusion") == "success":
            d["ok"] += 1
        elif r.get("conclusion") == "failure":
            d["fail"] += 1

    out = {
        "generated_at": now.isoformat(),
        "window_days": WINDOW_DAYS,
        "sample": total == 0,
        "deploy_frequency_per_week": round(deploy_freq, 2),
        "change_failure_rate": round(cfr, 3),
        "mttr_hours": round(mttr, 2),
        "lead_time_hours": round(lead, 2),
        "daily": list(daily.values()),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
