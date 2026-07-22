# Antigravity Finance - Premium Budget Manager

Antigravity Finance is a professional-grade, high-performance budget management web application. It features a modern **FastAPI** backend in Python, a premium **Glassmorphic UI Dashboard** (built with responsive Vanilla HTML, CSS, and JS), and a dynamic database layer powered by **SQLAlchemy** supporting both **SQLite** and **PostgreSQL**.

---

## Key Features
- **Dashboard Summary**: Real-time rolling counters for net balance, income, and expenses.
- **Interactive Metrics**: Dynamic SVG Donut chart displaying expenditures by categories.
- **Goal Progression**: Editable savings tracker with smooth progress animations.
- **CRUD Operations**: Live search, category and transaction type filtering, and smooth transactions deletion.
- **Docker-Ready**: Packaged with a production-optimized `Dockerfile` and `docker-compose.yml` for multi-service setup.
- **Flexible Storage**: Dynamic engine switching (default SQLite file storage, switch to external PostgreSQL simply via environment variables).

---

## 1. Running Locally (Without Docker)

### Prerequisites
- Python 3.9 or higher installed.

### Setup Steps
1. **Navigate to Project Directory**:
   ```bash
   cd finance-app
   ```

2. **Create and Activate a Virtual Environment**:
   - **Linux/macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Server**:
   ```bash
   python server.py
   ```
   The backend will auto-initialize an SQLite database file `finance.db` in the project root folder.
   Open your browser and visit: [http://localhost:8000](http://localhost:8000)
   To view the auto-generated Swagger API documentation, visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 2. Running in a Docker Container

### Build the Docker Image
To package the entire application (FastAPI backend + frontend files) into a self-contained container:
```bash
docker build -t finance-app .
```

### Option A: Run Container using Local SQLite (Default)
To run the container and persist your data across container restarts using a local SQLite file, mount a volume mapping a local path to the database location:
```bash
docker run -d \
  -p 8000:8000 \
  --name my-finance-app \
  -v "$(pwd)":/app \
  finance-app
```
*Note: Mounting the directory maps `finance.db` inside the container to your host machine's directory.*

### Option B: Run Container connecting to an External PostgreSQL Database
You can direct the container to use an external PostgreSQL database by passing the `DATABASE_URL` environment variable:
```bash
docker run -d \
  -p 8000:8000 \
  --name my-finance-app \
  -e DATABASE_URL="postgresql://user:password@host:port/database_name" \
  finance-app
```

---

## 3. Running Multi-Container Environment (Docker Compose)

For a fully automated deployment featuring a PostgreSQL database container and the FastAPI app container running side-by-side, use Docker Compose:

```bash
docker-compose up -d
```

### Services launched:
1. `db`: A PostgreSQL container exposed on port `5432` with database volumes mapped locally to preserve records.
2. `web`: The FastAPI server built from the local `Dockerfile` and configured to connect directly to the postgres `db` service.

To shut down and cleanup services:
```bash
docker-compose down
```

---

## 4. Connecting to an External/Remote Database (Configuration)

The application automatically checks for the `DATABASE_URL` environment variable on start. You can define this in your local terminal session or inside a `.env` file in the root project folder:

### PostgreSQL Connection String format:
Create a `.env` file:
```env
DATABASE_URL=postgresql://db_user:db_password@db_host:5432/db_name
```

If the `DATABASE_URL` starts with `postgresql://` (or `postgres://`), the database engine dynamically switches drivers, updates the schema tables, and establishes connections to the external server. The Database Connection card on the web frontend UI will dynamically update to reflect the engine type as **PostgreSQL**.
If no variable is specified, the application defaults to creating and using the local SQLite file (`finance.db`).
