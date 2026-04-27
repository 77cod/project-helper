export function buildSectionCards(report) {
  return [
    {
      key: "overview",
      title: "项目概述",
      content: `${report.overview?.title || "未命名项目"}\n\n${report.overview?.summary || ""}`.trim(),
    },
    {
      key: "tech_stack",
      title: "技术栈",
      content: [
        `语言：${(report.tech_stack?.languages || []).join("、") || "未知"}`,
        `框架：${(report.tech_stack?.frameworks || []).join("、") || "未识别"}`,
      ].join("\n"),
    },
    {
      key: "reading_guide",
      title: "阅读建议",
      content: [
        `难度：${report.reading_guide?.difficulty || "unknown"}`,
        ...((report.reading_guide?.steps || []).map((step, index) => `${index + 1}. ${step}`)),
      ].join("\n"),
    },
    {
      key: "directory_structure",
      title: "目录结构",
      language: "plaintext",
      content: `\`\`\`\n${report.directory_structure?.tree || "暂无目录树"}\n\`\`\``,
    },
    {
      key: "core_modules",
      title: "核心模块",
      content: (report.core_modules || [])
        .map((module) => `- \`${module.path}\`：${module.role}`)
        .join("\n"),
    },
    {
      key: "data_flow",
      title: "数据流",
      content: (report.data_flow?.steps || []).map((step, index) => `${index + 1}. ${step}`).join("\n"),
    },
    {
      key: "design_patterns",
      title: "设计模式",
      content: (report.design_patterns?.patterns || []).map((pattern) => `- ${pattern}`).join("\n"),
    },
  ];
}
