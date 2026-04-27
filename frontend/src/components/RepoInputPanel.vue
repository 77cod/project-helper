<script setup>
import { ref } from "vue";

const props = defineProps({
  loading: Boolean,
});

const emit = defineEmits(["submit"]);
const repoUrl = ref("https://github.com/tiangolo/fastapi");

function onSubmit() {
  emit("submit", repoUrl.value);
}
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <p class="eyebrow">Project Helper</p>
      <h1>像追番一样读懂开源项目</h1>
      <p class="hero-text">
        输入公开 GitHub 仓库地址，系统会自动克隆、分析源码、生成小白友好的报告，还能继续追问具体实现。
      </p>
    </div>

    <form class="hero-form" @submit.prevent="onSubmit">
      <label class="field-label" for="repo-url">GitHub 仓库地址</label>
      <input
        id="repo-url"
        v-model="repoUrl"
        class="url-input"
        type="url"
        placeholder="https://github.com/owner/repo"
      />
      <button class="cta-button" type="submit" :disabled="loading">
        {{ loading ? "分析进行中..." : "开始分析" }}
      </button>
    </form>
  </section>
</template>
