# 🤖 WorkspaceGPT

**WorkspaceGPT** is an AI-powered workspace assistant built using the **Model Context Protocol (MCP)**. It demonstrates how Large Language Models (LLMs) can dynamically discover and invoke tools exposed by independent MCP servers instead of relying on hardcoded integrations.

The project serves as a modern reference implementation of an MCP-powered AI application with a modular FastAPI backend, multiple MCP servers, and a lightweight web interface for exploring available tools and executing them.

---

## ✨ Features

* 🔌 **Model Context Protocol (MCP)** integration
* 🤖 AI-ready backend designed for LLM tool calling
* 📂 Filesystem MCP Server
* 🗄️ SQLite MCP Server
* 📝 Notes MCP Server
* 🐙 GitHub MCP Server
* 🌤️ Weather MCP Server
* ⚡ FastAPI backend with REST APIs
* 🎨 Lightweight browser interface
* 🔍 Dynamic MCP server discovery
* 🛠️ Tool discovery and execution
* 📦 Docker support
* ⚙️ Environment-based configuration

---

# 🏗️ Architecture

```text
                        User
                          │
                          ▼
                  Browser Frontend
                          │
                          ▼
                  FastAPI Backend
                          │
                    MCP Client Layer
                          │
        ┌───────────┬───────────┬───────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
 Filesystem      SQLite      GitHub      Notes      Weather
 MCP Server     MCP Server   MCP Server  MCP Server MCP Server
```

Each MCP server is an independent process exposing tools that can be discovered and invoked dynamically by the backend.

---

# 📁 Project Structure

```text
workspace-gpt/
│
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Configuration and settings
│   │   ├── database/      # SQLAlchemy engine and sessions
│   │   ├── mcp/           # MCP client implementation
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   │
│   └── main.py
│
├── frontend/
│   ├── index.html
│   └── src/
│
├── mcp_servers/
│   ├── filesystem_server/
│   ├── github_server/
│   ├── notes_server/
│   ├── sql_server/
│   └── weather_server/
│
├── docker-compose.yml
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

* Python 3.12+
* Git
* Docker (optional)

---

## Clone the Repository

```bash
git clone https://github.com/rohitkanderi/WorkspaceGPT.git

cd WorkspaceGPT/workspace-gpt/backend
```

---

## Create a Virtual Environment

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Copy the example environment file.

```bash
cp .env.example .env
```

For Windows:

```cmd
copy .env.example .env
```

---

## Configure MCP Servers

Set the environment variable:

```text
MCP_SERVER_CONFIG=MCP_SERVER_CONFIG.example.json
```

This configuration launches local stdio MCP servers for:

| Server     | Description                                    |
| ---------- | ---------------------------------------------- |
| Filesystem | Read, write, search and manage workspace files |
| SQLite     | Inspect and query a local SQLite database      |
| Notes      | Create, search and manage notes                |
| GitHub     | Access GitHub repository information           |
| Weather    | Retrieve weather data using wttr.in            |

---

## Start the Backend

```bash
uvicorn main:app --reload
```

Open:

```
http://localhost:8000
```

---

# 🐳 Running with Docker

```bash
docker compose up --build
```

The application will be available at:

```
http://localhost:8000
```

---

# 📡 REST API

| Method | Endpoint                      | Description                 |
| ------ | ----------------------------- | --------------------------- |
| GET    | `/api/health`                 | Health check                |
| GET    | `/api/mcp/servers`            | List configured MCP servers |
| POST   | `/api/mcp/servers/connect`    | Connect to an MCP server    |
| POST   | `/api/mcp/servers/disconnect` | Disconnect an MCP server    |
| POST   | `/api/mcp/tools/discover`     | Discover available tools    |
| GET    | `/api/mcp/tools`              | List discovered tools       |
| POST   | `/api/mcp/tools/call`         | Execute an MCP tool         |

---

# 🧩 Included MCP Servers

## 📂 Filesystem

* List directories
* Read files
* Write files
* Search files

---

## 🗄️ SQLite

* Inspect database schema
* Execute SQL queries
* Explore tables

---

## 📝 Notes

* Create notes
* Search notes
* List notes
* Delete notes

---

## 🐙 GitHub

* Browse repositories
* View commits
* Inspect issues
* Explore pull requests

---

## 🌤️ Weather

* Current weather
* Short forecasts

---

# 💡 Example Workflow

1. Start the backend.
2. The backend launches and connects to the configured MCP servers.
3. Discover available tools through the API or UI.
4. Execute a tool such as reading a file or querying SQLite.
5. Return structured results that can be consumed by an LLM-powered assistant.

---

# 🛣️ Roadmap

* [ ] React + TypeScript frontend
* [ ] LLM integration (OpenAI/Gemini)
* [ ] Streaming chat interface
* [ ] Authentication (JWT)
* [ ] Conversation history
* [ ] PostgreSQL support
* [ ] Docker production deployment
* [ ] Tool execution history
* [ ] Role-based access control
* [ ] Multi-agent workflows

---

# 🛠️ Tech Stack

* **Backend:** FastAPI
* **Language:** Python 3.12+
* **Protocol:** Model Context Protocol (MCP)
* **Database:** SQLite / SQLAlchemy
* **Validation:** Pydantic v2
* **Frontend:** HTML, JavaScript, CSS
* **Containerization:** Docker
* **Server:** Uvicorn

---

## ⭐ Why This Project?

WorkspaceGPT demonstrates how modern AI applications can use the **Model Context Protocol (MCP)** to dynamically discover and invoke tools, enabling modular, extensible, and scalable AI assistants without tightly coupling tool implementations to the application logic.
