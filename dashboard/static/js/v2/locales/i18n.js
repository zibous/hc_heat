// i18n.js - Lädt Sprachen dynamisch nach Bedarf
let currentLang = localStorage.getItem('dashboard-lang') || navigator.language.substring(0, 2) || 'de';
let loadedTranslations = {};

// Erlaubte Sprachen definieren, um Fehler bei falschen Browser-Sprachen zu vermeiden
const SUPPORTED_LANGUAGES = ['de', 'en', 'fr', 'it'];
if (!SUPPORTED_LANGUAGES.includes(currentLang)) currentLang = 'de';

export function getLang() {
  return currentLang;
}

// 🌟 Lädt die Sprachdatei dynamisch zur Laufzeit
export async function loadLanguage(lng) {
  if (!SUPPORTED_LANGUAGES.includes(lng)) lng = 'de';
  try {
    const module = await import(`./locales/${lng}.js`);
    loadedTranslations = module.default;
    currentLang = lng;
    localStorage.setItem('dashboard-lang', lng);
  } catch (err) {
    console.error(`Sprachdatei für ${lng} konnte nicht geladen werden`, err);
  }
}

// Gibt die passende Übersetzung oder Funktion zurück
export function t(path) {
  const keys = path.split('.');
  let result = loadedTranslations;

  for (const key of keys) {
    if (result && result[key] !== undefined) {
      result = result[key];
    } else {
      return path; // Fallback: Zeige Key, falls Übersetzung fehlt
    }
  }
  return result;
}

// Sprache wechseln und UI informieren
export async function changeLanguage(lng) {
  await loadLanguage(lng);
  document.dispatchEvent(new CustomEvent('languageChanged'));
}
