# Lumerath Foundation

Monorepo skeleton for the Codex + AI + Render stack.

## Apps
- **apps/api** – Express API. Routes:
  - \GET /entries/:id\
  - \POST /render\ → writes a placeholder artifact into \storage/generated/<entry>/\

## Storage
- **storage/codex** – versioned .json entries
- **storage/generated** – render outputs (placeholder receipts now)

## Quickstart
1. \cp .env.example .env\
2. \
pm run dev:api\
3. GET \http://localhost:7070/entries/braid-of-mirrors\
4. POST \http://localhost:7070/render\ with:
   \\\json
   { "entryId":"braid-of-mirrors", "template":"parchment", "width":1080, "height":1350, "watermark":true }
   \\\
5. Check \storage/generated/braid-of-mirrors/\ for the output file.
