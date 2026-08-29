/* audio.js — Korean text-to-speech via the browser's speechSynthesis (ko-KR).
   Dependency-free: no-ops gracefully when speech synthesis is unavailable. */
(function () {
  function speak(text, opts) {
    if (!('speechSynthesis' in window)) return;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    var u = new SpeechSynthesisUtterance(String(text || ''));
    u.lang = 'ko-KR';
    u.rate = (opts && opts.rate) || 0.9;
    u.pitch = 1;
    try {
      var vs = window.speechSynthesis.getVoices();
      for (var i = 0; i < vs.length; i++) {
        if (/^ko(-|_|$)/i.test(vs[i].lang)) { u.voice = vs[i]; break; }
      }
    } catch (e) {}
    try { window.speechSynthesis.speak(u); } catch (e) {}
  }
  window.speakKo = speak;
  // Warm the voice list (populated asynchronously on some browsers).
  if ('speechSynthesis' in window) {
    try { window.speechSynthesis.getVoices(); } catch (e) {}
  }
})();
