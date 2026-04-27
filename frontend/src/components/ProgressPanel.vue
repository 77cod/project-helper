<script setup>
defineProps({
  progress: {
    type: Object,
    default: () => null,
  },
});
</script>

<template>
  <section v-if="progress" class="panel progress-panel">
    <div class="panel-heading">
      <h2>分析进度</h2>
      <span class="panel-note">{{ progress.status }}</span>
    </div>

    <div class="progress-track">
      <div class="progress-bar" :style="{ width: `${progress.progress || 0}%` }"></div>
    </div>
    <p class="progress-step">{{ progress.step }}</p>
  </section>
</template>
