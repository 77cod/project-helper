<script setup>
import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js/lib/core";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import plaintext from "highlight.js/lib/languages/plaintext";
import python from "highlight.js/lib/languages/python";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import { computed } from "vue";

import { buildSectionCards } from "../utils/report";

const props = defineProps({
  report: {
    type: Object,
    default: null,
  },
});

hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("json", json);
hljs.registerLanguage("plaintext", plaintext);
hljs.registerLanguage("xml", xml);

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code, language) {
    if (language && hljs.getLanguage(language)) {
      return `<pre class="hljs"><code>${hljs.highlight(code, { language }).value}</code></pre>`;
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(code)}</code></pre>`;
  },
});

const cards = computed(() => (props.report ? buildSectionCards(props.report) : []));

function render(content) {
  return DOMPurify.sanitize(md.render(content || ""));
}
</script>

<template>
  <section class="panel report-panel">
    <div class="panel-heading">
      <h2>分析报告</h2>
      <span class="panel-note">小白友好版</span>
    </div>

    <div v-if="!report" class="empty-state">
      <p>分析完成后，报告会出现在这里。</p>
    </div>

    <div v-else class="report-grid">
      <article v-for="card in cards" :key="card.key" class="report-card">
        <h3>{{ card.title }}</h3>
        <div class="markdown-body" v-html="render(card.content)"></div>
      </article>
    </div>
  </section>
</template>
