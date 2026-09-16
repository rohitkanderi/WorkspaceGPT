const JSON_HEADERS = { "Content-Type": "application/json" };

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function getHealth() {
  return request("/api/health");
}

export function listServers() {
  return request("/api/mcp/servers");
}

export function connectServers() {
  return request("/api/mcp/servers/connect", { method: "POST" });
}

export function addServer(payload) {
  return request("/api/mcp/servers", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
}

export function discoverTools() {
  return request("/api/mcp/tools/discover", { method: "POST" });
}

export function listTools() {
  return request("/api/mcp/tools");
}

export function callTool(payload) {
  return request("/api/mcp/tools/call", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
}
