# WorkspaceGPT

WorkspaceGPT is an early-stage AI workspace assistant built around the Model
Context Protocol (MCP). It includes a FastAPI backend, local stdio MCP servers,
and a static browser UI for inspecting servers, discovering tools, and calling
tools.

## Project Structure

```text
workspace-gpt/
  backend/
    app/
      api/          FastAPI routers
      core/         settings and configuration
      database/     async SQLAlchemy engine/session/base
      mcp/          MCP client
      models/       SQLAlchemy models
      schemas/      Pydantic v2 schemas
      services/     app services
    main.py         ASGI entry point
  frontend/
    index.html      static UI served by FastAPI
    src/            browser JavaScript and CSS
  mcp_servers/
    filesystem_server/
    github_server/
    notes_server/
    sql_server/
    weather_server/
```

## Run Locally

Use Python 3.12 or newer.

```bash
cd workspace-gpt/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Open <http://localhost:8000>.

## MCP Configuration

The backend reads MCP server definitions from `MCP_SERVER_CONFIG`. For local
development, set it to:

```text
MCP_SERVER_CONFIG=MCP_SERVER_CONFIG.example.json
```

The example config starts local stdio servers for:

- `filesystem`: list, read, write, and search files under `WORKSPACE_ROOT`.
- `sqlite`: inspect and query a local SQLite database.
- `notes`: create, list, search, and delete local notes.
- `github`: read public or token-authenticated GitHub repository data.
- `weather`: fetch current weather and compact forecasts from wttr.in.

## API

- `GET /api/health`
- `GET /api/mcp/servers`
- `POST /api/mcp/servers/connect`
- `POST /api/mcp/servers/disconnect`
- `POST /api/mcp/tools/discover`
- `GET /api/mcp/tools`
- `POST /api/mcp/tools/call`

## Docker

```bash
docker compose up --build
```

The app will be available at <http://localhost:8000>.
