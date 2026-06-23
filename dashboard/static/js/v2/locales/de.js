export default {
  theme: {
    light: "☀️ Helles Design",
    dark: "🌙 Dunkles Design"
  },
  dashboard: {
    update: (date, time) => `Update: ${date} ${time}`,
    installed: (date) => `Installiert: ${date}`,
    fetch_failed: "Datenabruf fehlgeschlagen:"
  }
};
