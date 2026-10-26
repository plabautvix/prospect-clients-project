# Observabilidade

Os cinco serviços Python (`backend`, `maps-service`, `instagram-service`,
`whatsapp-sender`, `instagram-dm`) exportam **traces, métricas e logs** com
OpenTelemetry, por OTLP/HTTP, para o container `lgtm` do compose. Ele roda num
só processo o OpenTelemetry Collector, Tempo (traces), Loki (logs), Prometheus
(métricas) e Grafana.

```
serviço --OTLP/HTTP :4318--> lgtm (Collector) --> Tempo / Loki / Prometheus --> Grafana :3000
```

## Subir

```sh
docker compose up -d --build
```

Abra http://localhost:3000. O dashboard **Prospect Clients** fica na pasta de
mesmo nome (Dashboards). O Grafana local não pede login.

Para explorar livremente: **Explore**, escolhendo Tempo, Loki ou Prometheus.

## O que é coletado

### Traces

| Origem | Spans |
|---|---|
| backend | Uma por requisição HTTP (FastAPI) e uma por query (SQLAlchemy). `<tópico> publish` ao publicar no MQTT. |
| maps-service, instagram-service | `<tópico> process` ao receber o comando do MQTT, `maps scrape` / `instagram search` cobrindo a busca inteira, e as chamadas HTTP ao backend. |
| whatsapp-sender, instagram-dm | `<canal> deliver` por mensagem, com as chamadas ao WAHA e ao backend dentro. |

O contexto do trace é propagado entre serviços, então uma operação aparece
como **um trace só**:

- **HTTP** (workers para o backend): cabeçalho `traceparent`, injetado pela
  instrumentação do `requests` e lido pela do FastAPI.
- **MQTT** (backend para as buscas): o MQTT 3.1.1 não tem cabeçalhos, então o
  `traceparent` viaja no próprio payload, na chave `trace_context`. Os
  consumidores ignoram chaves que não conhecem.
- **Threads**: a busca roda numa thread separada, que não herda o contexto. O
  contexto da mensagem MQTT é capturado antes e entregue à thread.

Exemplo: o usuário inicia uma busca no Maps e o trace mostra
`POST /automations/...` → `prospect/maps publish` → `prospect/maps process` →
`maps scrape` → `POST /leads/` (no backend) → `INSERT ...`.

### Métricas

Além das automáticas (`http_server_request_duration_seconds` no backend,
`http_client_request_duration_seconds` nos workers), as de negócio:

| Métrica (nome no Prometheus) | Serviço | Labels |
|---|---|---|
| `prospect_leads_registered_total` | backend | `source` |
| `prospect_campaign_messages_queued_total` | backend | `channel` |
| `prospect_outbox_claims_total` | backend | `channel`, `result` (`message`, `paced`, `in_flight`, `empty`) |
| `prospect_outbox_results_total` | backend | `channel`, `outcome` (`sent`, `failed`, `retry`, `release`) |
| `prospect_search_leads_found_total` | maps-service, instagram-service | `source` |
| `prospect_sender_delivery_duration_seconds` | whatsapp-sender, instagram-dm | `channel`, `outcome` |

O label `job` traz o nome do serviço.

### Logs

Todo `logging` dos serviços continua no console e também vai para o Loki, com o
`trace_id` do span em que foi escrito. No Grafana, um log abre o trace dele e um
span abre os logs dele. As queries SQL que o `echo=True` imprime ficam fora do
Loki, porque já estão nos traces.

## Ligar e desligar

O código só liga o OpenTelemetry quando `OTEL_EXPORTER_OTLP_ENDPOINT` está
definida. No compose ela vem da âncora `x-otel-env`; tirar `<<: *otel-env` de
um serviço desliga a telemetria dele. Os testes não definem a variável, então
rodam sem telemetria e sem precisar do collector.

Para um serviço rodando fora do Docker, direto na máquina, com o `lgtm` de pé:

```sh
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 python main.py
```

Variáveis úteis (padrão OpenTelemetry):

| Variável | Uso |
|---|---|
| `OTEL_SERVICE_NAME` | Troca o nome do serviço. |
| `OTEL_METRIC_EXPORT_INTERVAL` | Intervalo de envio das métricas, em ms (15000 no compose). |
| `OTEL_TRACES_SAMPLER` / `OTEL_TRACES_SAMPLER_ARG` | Amostragem, por exemplo `parentbased_traceidratio` e `0.1`. |
| `GRAFANA_PORT`, `OTLP_HTTP_PORT` | Portas do `lgtm` no host (3000 e 4318). |

## Arquivos

- `observability/grafana/dashboards/prospect.json`: o dashboard. Dá para
  editar no Grafana, exportar o JSON e salvar aqui.
- `observability/grafana/provisioning/prospect.yaml`: diz ao Grafana para
  carregar a pasta acima.
- `*/src/telemetry.py` e `back_end/.../configurations/telemetry.py`: o setup
  em cada serviço.

## Cuidados

- `opentelemetry-instrumentation-sqlalchemy` 0.66b1 só aceita
  `sqlalchemy < 2.1`. O `poetry.lock` fixa a 2.0.44. Ao subir o SQLAlchemy para
  2.1, suba também a instrumentação, ou as queries somem dos traces (o backend
  loga um ERROR avisando).
- O `lgtm` é para desenvolvimento: guarda tudo num volume local
  (`lgtm-data`), sem autenticação, e escuta só em `127.0.0.1`. Em produção, o
  mesmo código exporta para qualquer backend OTLP trocando
  `OTEL_EXPORTER_OTLP_ENDPOINT`.
