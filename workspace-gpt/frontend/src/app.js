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
const detailNameEl = document.querySelector("#detail-name");
const detailDescriptionEl = document.querySelector("#detail-description");
const detailServerEl = document.querySelector("#detail-server");
const detailUsageEl = document.querySelector("#detail-usage");
const toolCountEl = document.querySelector("#tool-count");
const resultStatusEl = document.querySelector("#result-status");
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

function usageText(tool) {
  const required = tool?.input_schema?.required || [];
  if (!required.length) {
    return "No required arguments. The suggested JSON is ready to cast as-is.";
  }
  return `Provide ${required.map((name) => `"${name}"`).join(", ")} before casting this tool.`;
}

function selectTool(tool) {
  if (!tool) return;
  document.querySelector("#tool-name").value = tool.name;
  document.querySelector("#server-name").value = tool.server_name;
  document.querySelector("#arguments").value = pretty(sampleArguments(tool.input_schema));
  detailServerEl.textContent = `${tool.server_name} / discovered instrument`;
  detailNameEl.textContent = tool.name;
  detailDescriptionEl.textContent = tool.description || "A capable instrument waiting for your direction.";
  detailUsageEl.textContent = usageText(tool);
  document.querySelectorAll(".tool-row").forEach((row) => row.classList.toggle("is-selected", row.dataset.key === toolKey(tool)));
  const detailPanel = document.querySelector("#tool-detail");
  detailPanel.classList.remove("is-revealing");
  void detailPanel.offsetWidth;
  detailPanel.classList.add("is-revealing");
  resultStatusEl.textContent = "Ready to cast";
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
    toolCountEl.textContent = "0 tools discovered";
    toolsEl.innerHTML = '<p class="empty">No tools discovered yet.</p>';
    return;
  }
  toolCountEl.textContent = `${tools.length} tool${tools.length === 1 ? "" : "s"} discovered`;
  toolsEl.innerHTML = tools
    .map((tool) => {
      const key = toolKey(tool);
      toolsByKey.set(key, tool);
      return `
        <button class="tool-row" data-key="${escapeHtml(key)}">
          <span class="tool-glyph">✧</span>
          <span class="tool-row-copy"><strong>${escapeHtml(tool.name)}</strong><small>${escapeHtml(tool.server_name)}</small></span>
          <span class="tool-arrow">→</span>
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
  resultEl.textContent = "The realms are opening...";
  resultStatusEl.textContent = "Connecting";
  try {
    await connectServers();
    resultEl.textContent = "The realms are connected.";
    resultStatusEl.textContent = "Ready";
    await refresh();
  } catch (error) {
    resultEl.textContent = error.message;
    resultStatusEl.textContent = "Connection faltered";
  }
});

document.querySelector("#discover").addEventListener("click", async () => {
  resultEl.textContent = "The library is opening...";
  resultStatusEl.textContent = "Discovering";
  try {
    const tools = await discoverTools();
    renderTools(tools);
    await refresh();
    resultEl.textContent = "Choose an instrument from the library to begin.";
    resultStatusEl.textContent = "Standing by";
  } catch (error) {
    resultEl.textContent = error.message;
    resultStatusEl.textContent = "Discovery faltered";
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
  selectTool(tool);
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
  resultEl.textContent = "The spell is taking shape...";
  resultStatusEl.textContent = "Casting...";
  try {
    const serverName = document.querySelector("#server-name").value.trim();
    const toolName = document.querySelector("#tool-name").value.trim();
    const args = JSON.parse(document.querySelector("#arguments").value || "{}");
    const tool = selectedTool(serverName, toolName);
    const missing = missingRequiredArguments(tool, args);
    if (missing.length) {
      resultEl.textContent = `Missing required arguments: ${missing.join(", ")}`;
      resultStatusEl.textContent = "Needs ingredients";
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
    resultStatusEl.textContent = "Cast complete";
  } catch (error) {
    resultEl.textContent = error.message;
    resultStatusEl.textContent = "The spell faltered";
  }
});

refresh();
