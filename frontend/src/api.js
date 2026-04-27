const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "请求失败");
  }

  return response.json();
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export function analyzeProject(repoUrl) {
  return request("/api/projects/analyze", {
    method: "POST",
    body: JSON.stringify({ repo_url: repoUrl }),
  });
}

export function fetchProjects() {
  return request("/api/projects");
}

export function fetchReport(projectId) {
  return request(`/api/projects/${projectId}/report`);
}

export function createChatSession(projectId, title = "源码问答") {
  return request("/api/chat/sessions", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, title }),
  });
}

export async function streamQuestion(sessionId, question, handlers) {
  const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok || !response.body) {
    throw new Error("流式问答请求失败");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) {
        continue;
      }
      handlers?.onEvent?.(JSON.parse(dataLine.slice(6)));
    }
  }
}
