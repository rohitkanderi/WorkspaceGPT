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
const toolsByKey = new Map();

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sampleValue(name, property = {}) {
  if (property.default !== undefined) {
    return property.default;
  }
  if (property.type === "integer" || property.type === "number") {
    return 0;
  }
  if (property.type === "boolean") {
    return false;
  }
  if (property.type === "array") {
    return [];
  }
  if (property.type === "object") {
    return {};
  }
  if (name === "owner") {
    return "openai";
  }
  if (name === "repo") {
    return "openai-python";
  }
  if (name === "location") {
    return "Mumbai";
  }
  if (name === "query") {
    return "workspace";
  }
  if (name === "title") {
    return "New note";
  }
  if (name === "body") {
    return "Write your note here.";
  }
  return "";
}

function sampleArguments(schema = {}) {
  const properties = schema.properties || {};
  const required = new Set(schema.required || []);
  const args = {};
  for (const [name, property] of Object.entries(properties)) {
    if (required.has(name) || property.default !== undefined) {
      args[name] = sampleValue(name, property);
    }
  }
  return args;
}

function selectedTool(serverName, toolName) {
  if (serverName) {
    return toolsByKey.get(`${serverName}:${toolName}`);
  }
  return Array.from(toolsByKey.values()).find((tool) => tool.name === toolName);
}

function missingRequiredArguments(tool, args) {
  const required = tool?.input_schema?.required || [];
  return required.filter((name) => {
    const value = args[name];
    return value === undefined || value === null || value === "";
  });
}

function toolKey(tool) {
  return `${tool.server_name}:${tool.name}`;
}

function renderServers(servers) {
  if (!servers.length) {
    serversEl.innerHTML = '<p class="empty">No MCP servers configured.</p>';
    return;
  }
  serversEl.innerHTML = servers
    .map(
      (server) => `
        <button class="row server-row" data-server="${escapeHtml(server.name)}">
          <span>
            <strong>${escapeHtml(server.name)}</strong>
            <small>${escapeHtml(server.transport)} - ${server.tool_count} tools</small>
          </span>
          <span class="badge ${escapeHtml(server.status)}">${escapeHtml(server.status)}</span>
        </button>
      `,
    )
    .join("");
}

function renderTools(tools) {
  toolsByKey.clear();
  if (!tools.length) {
    toolsEl.innerHTML = '<p class="empty">No tools discovered yet.</p>';
    return;
  }
  toolsEl.innerHTML = tools
    .map((tool) => {
      const key = toolKey(tool);
      toolsByKey.set(key, tool);
      return `
        <button class="row tool-row" data-key="${escapeHtml(key)}">
          <span>
            <strong>${escapeHtml(tool.name)}</strong>
            <small>${escapeHtml(tool.server_name)}</small>
          </span>
          <span>${escapeHtml(tool.description || "")}</span>
        </button>
      `;
    })
    .join("");
}

async function refresh() {
  try {
    const [health, servers, tools] = await Promise.all([
      getHealth(),
      listServers(),
      listTools(),
    ]);
    healthEl.textContent = `${health.app} ${health.version} - ${health.status}`;
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
  const tool = toolsByKey.get(row.dataset.key);
  if (!tool) {
    return;
  }
  document.querySelector("#tool-name").value = tool.name;
  document.querySelector("#server-name").value = tool.server_name;
  document.querySelector("#arguments").value = pretty(sampleArguments(tool.input_schema));
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
    const toolName = document.querySelector("#tool-name").value.trim();
    const args = JSON.parse(document.querySelector("#arguments").value || "{}");
    const tool = selectedTool(serverName, toolName);
    const missing = missingRequiredArguments(tool, args);
    if (missing.length) {
      resultEl.textContent = `Missing required arguments: ${missing.join(", ")}`;
      return;
    }
    const payload = {
      tool_name: toolName,
      arguments: args,
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
