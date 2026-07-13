import {
  callTool,
  connectServers,
  discoverTools,
  getHealth,
  listServers,
  listTools,
} from "./api.js";

const healthEl = document.querySelector("#health");
const serversEl = document.querySelector("#servers");
const toolsEl = document.querySelector("#tools");
const resultEl = document.querySelector("#result");
const form = document.querySelector("#tool-form");

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function renderServers(servers) {
  if (!servers.length) {
    serversEl.innerHTML = '<p class="empty">No MCP servers configured.</p>';
    return;
  }
  serversEl.innerHTML = servers
    .map(
      (server) => `
        <button class="row server-row" data-server="${server.name}">
          <span>
            <strong>${server.name}</strong>
            <small>${server.transport} · ${server.tool_count} tools</small>
          </span>
          <span class="badge ${server.status}">${server.status}</span>
        </button>
      `,
    )
    .join("");
}

function renderTools(tools) {
  if (!tools.length) {
    toolsEl.innerHTML = '<p class="empty">No tools discovered yet.</p>';
    return;
  }
  toolsEl.innerHTML = tools
    .map(
      (tool) => `
        <button class="row tool-row" data-tool="${tool.name}" data-server="${tool.server_name}">
          <span>
            <strong>${tool.name}</strong>
            <small>${tool.server_name}</small>
          </span>
          <span>${tool.description || ""}</span>
        </button>
      `,
    )
    .join("");
}

async function refresh() {
  try {
    const [health, servers, tools] = await Promise.all([
      getHealth(),
      listServers(),
      listTools(),
    ]);
    healthEl.textContent = `${health.app} ${health.version} · ${health.status}`;
    renderServers(servers);
    renderTools(tools);
  } catch (error) {
    healthEl.textContent = error.message;
  }
}

document.querySelector("#refresh").addEventListener("click", refresh);

document.querySelector("#connect-all").addEventListener("click", async () => {
  resultEl.textContent = "Connecting...";
  try {
    await connectServers();
    resultEl.textContent = "Connected.";
    await refresh();
  } catch (error) {
    resultEl.textContent = error.message;
  }
});

document.querySelector("#discover").addEventListener("click", async () => {
  resultEl.textContent = "Discovering tools...";
  try {
    const tools = await discoverTools();
    renderTools(tools);
    await refresh();
    resultEl.textContent = pretty(tools);
  } catch (error) {
    resultEl.textContent = error.message;
  }
});

toolsEl.addEventListener("click", (event) => {
  const row = event.target.closest(".tool-row");
  if (!row) {
    return;
  }
  document.querySelector("#tool-name").value = row.dataset.tool;
  document.querySelector("#server-name").value = row.dataset.server;
});

serversEl.addEventListener("click", (event) => {
  const row = event.target.closest(".server-row");
  if (!row) {
    return;
  }
  document.querySelector("#server-name").value = row.dataset.server;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultEl.textContent = "Running...";
  try {
    const serverName = document.querySelector("#server-name").value.trim();
    const payload = {
      tool_name: document.querySelector("#tool-name").value.trim(),
      arguments: JSON.parse(document.querySelector("#arguments").value || "{}"),
    };
    if (serverName) {
      payload.server_name = serverName;
    }
    resultEl.textContent = pretty(await callTool(payload));
  } catch (error) {
    resultEl.textContent = error.message;
  }
});

refresh();
