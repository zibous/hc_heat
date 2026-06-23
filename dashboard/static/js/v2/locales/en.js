export default {
  theme: {
    light: "☀️ Light Design",
    dark: "🌙 Dark Design"
  },
  dashboard: {
    update: (date, time) => `Update: ${date} ${time}`,
    installed: (date) => `Installed: ${date}`,
    fetch_failed: "Data fetch failed:"
  }
};
