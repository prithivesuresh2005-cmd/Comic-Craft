(() => {
  const panels = [...document.querySelectorAll('.reel-panel')];
  if (!panels.length) return;

  const bg = document.getElementById('reelBg');
  const progress = document.getElementById('progressBar');
  const label = document.getElementById('panelLabel');
  const playBtn = document.getElementById('playBtn');
  const playIcon = document.getElementById('playIcon');
  const playText = document.getElementById('playText');
  let current = 0;
  let playing = true;
  let timer = null;
  const delay = 5500;

  function show(index) {
    current = (index + panels.length) % panels.length;
    panels.forEach((panel, i) => panel.classList.toggle('active', i === current));
    const image = panels[current].querySelector('img');
    if (image && bg) {
      bg.style.backgroundImage = `url("${image.src}")`;
      bg.classList.remove('zoom');
      void bg.offsetWidth;
      bg.classList.add('zoom');
    }
    if (progress) progress.style.width = `${((current + 1) / panels.length) * 100}%`;
    if (label) label.textContent = `Panel ${current + 1} of ${panels.length}`;
  }

  function next() { show(current + 1); }
  function prev() { show(current - 1); }

  function stopTimer() {
    if (timer) clearInterval(timer);
    timer = null;
  }

  function startTimer() {
    stopTimer();
    timer = setInterval(next, delay);
  }

  function updateButton() {
    if (!playBtn) return;
    playIcon.textContent = playing ? 'Ⅱ' : '▶';
    playText.textContent = playing ? 'Pause' : 'Play';
    playBtn.setAttribute('aria-label', playing ? 'Pause' : 'Play');
  }

  playBtn?.addEventListener('click', () => {
    playing = !playing;
    updateButton();
    playing ? startTimer() : stopTimer();
  });
  document.getElementById('nextBtn')?.addEventListener('click', () => { next(); if (playing) startTimer(); });
  document.getElementById('prevBtn')?.addEventListener('click', () => { prev(); if (playing) startTimer(); });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight') next();
    if (event.key === 'ArrowLeft') prev();
    if (event.code === 'Space') { event.preventDefault(); playBtn?.click(); }
    if (playing && (event.key === 'ArrowRight' || event.key === 'ArrowLeft')) startTimer();
  });

  let touchStart = 0;
  document.addEventListener('touchstart', e => { touchStart = e.changedTouches[0].screenX; }, {passive:true});
  document.addEventListener('touchend', e => {
    const diff = e.changedTouches[0].screenX - touchStart;
    if (Math.abs(diff) > 50) { diff < 0 ? next() : prev(); if (playing) startTimer(); }
  }, {passive:true});

  show(0);
  updateButton();
  startTimer();
})();
