# Ket noi MySQL

Mac dinh project chay MySQL o port `3306`.

## Chay stack

```bash
docker compose up -d --build
docker compose ps
```

Neu can reset database tu dau:

```bash
docker compose down -v
docker compose up -d --build
```

## Thong tin ket noi

```text
Host: localhost
Port: 3306
Database: quan_ly_chi_nhanh
User: techstore
Password: MyPass@2025
Root password: RootPass@2025
```

Backend trong Docker ket noi bang host noi bo:

```env
DB_ENGINE=mysql
DB_HOST=mysql
DB_PORT=3306
DB_USER=techstore
DB_PASSWORD=MyPass@2025
DB_NAME=quan_ly_chi_nhanh
```

## Kiem tra nhanh

```bash
docker compose exec mysql mysql -utechstore -pMyPass@2025 quan_ly_chi_nhanh
```

Trong MySQL shell:

```sql
SHOW TABLES;
SELECT * FROM chi_nhanh;
```

SQL Server van duoc giu trong `docker-compose.yml`, nhung chi chay khi bat profile:

```bash
docker compose --profile sqlserver up -d sqlserver mssql-init
```
