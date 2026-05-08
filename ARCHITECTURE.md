# Tech Store Distributed Layout

The application is split into three independent systems:

```text
tru_so/
  backend/
  frontend/
  service/

mysql/
  backend/
  frontend/
  service/

postgre/
  backend/
  frontend/
  service/
```

- `tru_so` is the headquarter system and connects to SQL Server.
- `mysql` is the CN01 branch system and connects to MySQL.
- `postgre` is the CN02 branch system and connects to PostgreSQL.
- Each `service` process is the integration boundary for talking to its local backend and peer services.

Service endpoints:

```text
GET /api/service/ping
GET /api/service/registry
GET /api/service/backend-health
GET /api/service/peers/health
```

Run everything:

```powershell
docker compose up -d --build --remove-orphans
```
