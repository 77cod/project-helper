<script setup>
import { ref } from "vue";

defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  disabled: Boolean,
  loading: Boolean,
});

const emit = defineEmits(["ask"]);
const question = ref("");

function submit() {
  if (!question.value.trim()) {
    return;
  }
  emit("ask", question.value);
  question.value = "";
}
</script>

<template>
  <section class="panel chat-panel">
    <div class="panel-heading">
      <h2>源码问答</h2>
      <span class="panel-note">Agent 会自己查文件</span>
    </div>

    <div class="chat-log">
      <article v-for="message in messages" :key="message.id" class="chat-message" :class="message.role">
        <strong>{{ message.role === "user" ? "你" : "助手" }}</strong>
        <p>{{ message.content }}</p>
        <ul v-if="message.references?.length" class="references">
          <li v-for="item in message.references" :key="item.path">{{ item.path }}</li>
        </ul>
      </article>
      <p v-if="messages.length === 0" class="empty-hint">试着问一句：“这个项目的入口在哪里？”</p>
    </div>

    <form class="chat-form" @submit.prevent="submit">
      <textarea
        v-model="question"
        class="chat-input"
        :disabled="disabled || loading"
        placeholder="继续追问源码细节..."
      ></textarea>
      <button class="secondary-button" type="submit" :disabled="disabled || loading">
        {{ loading ? "思考中..." : "发送问题" }}
      </button>
    </form>
  </section>
</template>
