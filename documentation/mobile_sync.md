# Mobile Sync Pipeline

The mobile apps now fetch a single Celery-backed snapshot so every feature sees the same data that powers the web experience.

## How it works

1. The iOS client calls `GET /api/mobile-sync/snapshot/`.
2. The view returns the most recent serialized payload (dashboard, records, stock analysis, chat, etc.).
3. If the snapshot is missing/expired, the endpoint also queues `generate_mobile_snapshot` via Celery.
4. The Celery task executes `MobileDataAssembler`, which reuses the existing aggregation services and stores the JSON payload in `MobileDataSnapshot`.
5. Clients may poll `GET /api/mobile-sync/snapshot/<scope>/` or call `POST /api/mobile-sync/snapshot/` with `{"refresh": true}` to force a refresh.

## Configuration

- `MOBILE_SYNC_TTL_SECONDS` (default 900) controls how long a snapshot stays “fresh”.
- Snapshots are keyed by user + scope (e.g. `all`, `dashboard+records`).
- Data is serialized via `apps/mobile_sync/services.MobileDataAssembler` to keep payloads ready for mobile consumption.

## Adding new sections

1. Extend `MobileDataAssembler.ALL_SECTIONS` and implement `_build_<section>()`.
2. Update the mobile client to request the new section if needed.
3. (Optional) expose it via the API by passing `sections` in the request.

Run `python manage.py makemigrations mobile_sync && python manage.py migrate` after editing the model.
