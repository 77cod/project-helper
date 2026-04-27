<script setup>
import { onMounted, ref } from "vue";

import ChatPanel from "./components/ChatPanel.vue";
import ProgressPanel from "./components/ProgressPanel.vue";
import ProjectList from "./components/ProjectList.vue";
import RepoInputPanel from "./components/RepoInputPanel.vue";
import ReportViewer from "./components/ReportViewer.vue";
import {
  analyzeProject,
  createChatSession,
  fetchProjects,
  fetchReport,
  getApiBaseUrl,
  streamQuestion,
} from "./api";

const projects = ref([]);
const activeProjectId = ref(null);
const report = ref(null);
const progress = ref(null);
const loading = ref(false);
const chatLoading = ref(false);
const chatMessages = ref([]);
const chatSessionId = ref(null);
const errorMessage = ref("");

let eventSource = null;

async function loadProjects() {
  projects.value = await fetchProjects();
}

async function ensureChatSession(projectId) {
  if (chatSessionId.value && activeProjectId.value === projectId) {
    return;
  }
  const session = await createChatSession(projectId, "默认问答");
  chatSessionId.value = session.id;
  chatMessages.value = [];
}

async function openProject(project) {
  activeProjectId.value = project.id;
  report.value = await fetchReport(project.id);
  progress.value = null;
  await ensureChatSession(project.id);
}

function connectProgress(runId, projectId) {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource(`${getApiBaseUrl()}/api/runs/${runId}/events`);

  eventSource.onmessage = async (event) => {
    const payload = JSON.parse(event.data);
    progress.value = payload;

    if (payload.status === "completed") {
      report.value = await fetchReport(projectId);
      activeProjectId.value = projectId;
      loading.value = false;
      eventSource.close();
      await ensureChatSession(projectId);
      await loadProjects();
    }
  };

  eventSource.onerror = () => {
    eventSource?.close();
  };
}

async function handleAnalyze(repoUrl) {
  loading.value = true;
  errorMessage.value = "";

  try {
    const result = await analyzeProject(repoUrl);
    activeProjectId.value = result.project_id;

    if (result.cached) {
      report.value = await fetchReport(result.project_id);
      progress.value = { status: "completed", progress: 100, step: "命中缓存，已直接加载报告" };
      loading.value = false;
      await ensureChatSession(result.project_id);
      await loadProjects();
      return;
    }

    progress.value = { status: result.status, progress: 15, step: "分析任务已创建，准备读取仓库..." };
    connectProgress(result.run_id, result.project_id);

    if (result.status === "completed") {
      report.value = await fetchReport(result.project_id);
      loading.value = false;
      await ensureChatSession(result.project_id);
      await loadProjects();
    }
  } catch (error) {
    loading.value = false;
    errorMessage.value = error.message || "分析失败";
  }
}

async function handleAsk(question) {
  if (!chatSessionId.value) {
    return;
  }

  chatLoading.value = true;
  const assistantId = `${Date.now()}-assistant`;
  chatMessages.value.push({ id: `${Date.now()}-user`, role: "user", content: question, references: [] });
  chatMessages.value.push({ id: assistantId, role: "assistant", content: "", references: [] });

  try {
    await streamQuestion(chatSessionId.value, question, {
      onEvent(payload) {
        const assistantMessage = chatMessages.value.find((item) => item.id === assistantId);
        if (!assistantMessage) {
          return;
        }
        if (payload.type === "meta") {
          assistantMessage.references = payload.references || [];
        }
        if (payload.type === "chunk") {
          assistantMessage.content += payload.content;
        }
      },
    });
  } catch (error) {
    const assistantMessage = chatMessages.value.find((item) => item.id === assistantId);
    if (assistantMessage) {
      assistantMessage.content = error.message || "问答失败";
    }
  } finally {
    chatLoading.value = false;
  }
}

onMounted(loadProjects);
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <ProjectList :projects="projects" :active-project-id="activeProjectId" @select="openProject" />
    </aside>

    <main class="main-stage">
      <RepoInputPanel :loading="loading" @submit="handleAnalyze" />
      <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
      <ProgressPanel :progress="progress" />
      <ReportViewer :report="report" />
    </main>

    <aside class="chat-column">
      <ChatPanel
        :messages="chatMessages"
        :disabled="!activeProjectId"
        :loading="chatLoading"
        @ask="handleAsk"
      />
    </aside>
  </div>
</template>
