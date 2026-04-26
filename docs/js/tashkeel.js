// Tashkeel (Arabic diacritical marks) toggle
// Unicode ranges:
//   U+064B–U+065F  standard Arabic harakat (fatha, kasra, damma, tanwin, shadda, sukoon, etc.)
//   U+0610–U+061A  extended Arabic marks
//   U+06D6–U+06DC  Quranic annotation signs

const TASHKEEL_REGEX = /[\u064B-\u065F\u0610-\u061A\u06D6-\u06DC]/g;

let tashkeelVisible = localStorage.getItem('tashkeel_pref') !== 'false';

function applyTashkeelState() {
  const btn = document.getElementById('tashkeel-toggle');
  document.querySelectorAll('[data-full-text]').forEach(el => {
    el.textContent = tashkeelVisible
      ? el.dataset.fullText
      : el.dataset.fullText.replace(TASHKEEL_REGEX, '');
  });
  if (btn) {
    btn.textContent = tashkeelVisible ? 'إخفاء التشكيل' : 'إظهار التشكيل';
  }
}

function toggleTashkeel() {
  tashkeelVisible = !tashkeelVisible;
  localStorage.setItem('tashkeel_pref', tashkeelVisible);
  applyTashkeelState();
}
