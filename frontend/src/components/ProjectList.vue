<script setup>
defineProps({
  projects: {
    type: Array,
    default: () => [],
  },
  activeProjectId: Number,
});

const emit = defineEmits(["select"]);
</script>

<template>
  <section class="panel glass-panel">
    <div class="panel-heading">
      <h2>项目历史</h2>
      <span class="panel-note">已分析项目会缓存</span>
    </div>

    <button
      v-for="project in projects"
      :key="project.id"
      class="project-item"
      :class="{ active: activeProjectId === project.id }"
      @click="emit('select', project)"
    >
      <strong>{{ project.name }}</strong>
      <span>{{ project.repo_url }}</span>
      <em>{{ project.status }}</em>
    </button>

    <p v-if="projects.length === 0" class="empty-hint">还没有历史项目，先分析一个仓库吧。</p>
  </section>
</template>
