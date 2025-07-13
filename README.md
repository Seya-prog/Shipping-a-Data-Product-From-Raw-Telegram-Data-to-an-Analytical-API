# Shipping a Data Product: From Raw Telegram Data to an Analytical API

This repository contains an end-to-end data pipeline that ingests public Telegram data, models it into a star-schema warehouse, enriches it with object-detection insights, and finally exposes clean data through a FastAPI analytical service.

## Repository Structure

```
├── app/                # Python source code (FastAPI, Dagster jobs, utils, etc.)
│   └── config.py       # Central settings loader (python-dotenv + Pydantic)
├── Dockerfile          # Container image for the application layer
├── docker-compose.yml  # Multi-service stack (PostgreSQL + App)
├── requirements.txt    # Python dependencies
├── .gitignore          # Files/directories to keep out of git
├── .dockerignore       # Files to exclude from Docker build context
├── example.env         # Template for environment variables (copy to `.env`)
└── README.md           # Project documentation (this file)
```

## Quick Start (Local Docker)

1. **Clone & setup secrets**
   ```bash
   cp example.env .env  # add your keys/passwords
   ```
2. **Build & run the stack**
   ```bash
   docker compose up --build
   ```
   * PostgreSQL* will be available on `${DB_PORT}` (5432 by default).
   * FastAPI docs* at `http://localhost:8000/docs` once Task 2+ are implemented.

3. **Stop containers**
   ```bash
   docker compose down -v
   ```

## Environment Variables (.env)
Parameter            | Description
-------------------- | -----------
`API_ID`, `API_HASH`, `BOT_TOKEN` | Telegram credentials for Telethon
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Postgres auth
`DB_PORT`            | Host port to expose Postgres (default 5432)

> **Security**: `.env` is git-ignored by default—never commit secrets.

## Next Steps
Task 0 (project setup) is complete. Subsequent tasks will cover:
1. **Data scraping** from Telegram → raw zone (Task 1)
2. **ELT transformations** with dbt (Task 2)
3. **Enrichment** via YOLOv8 (Task 3)
4. **Analytical API** with FastAPI (Task 4)
5. **Orchestration** using Dagster (Task 5)

---
Feel free to proceed to Task 1, or let me know if you need adjustments to the setup.
