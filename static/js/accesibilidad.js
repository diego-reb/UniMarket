document.addEventListener('DOMContentLoaded', () => {
  // Crear botón flotante
  const toggleBtn = document.createElement('button');
  toggleBtn.id = 'accesibility-toggle';
  toggleBtn.title = 'Opciones de accesibilidad';
  toggleBtn.innerHTML = '♿';
  document.body.appendChild(toggleBtn);

  // Crear panel
  const panel = document.createElement('div');
  panel.id = 'accesibility-panel';
  panel.innerHTML = `
    <button id="toggle-dark">Modo Claro</button>
    <button id="toggle-contrast">Alto contraste</button>
    <button id="toggle-font">Tipografía accesible</button>
    <button id="aumentar-texto"> Aum Texto+</button>
    <button id="disminuir-texto">Dism Texto-</button>
    <button id="toggle-grayscale">Escala de grises</button>
    <button id="toggle-guide">Guía de lectura</button>
    <button id="toggle-read">Lectura en voz alta</button>
  `;
  document.body.appendChild(panel);

  // Mostrar/ocultar panel
  toggleBtn.addEventListener('click', () => panel.classList.toggle('active'));
  document.addEventListener('click', e => {
    if (!panel.contains(e.target) && e.target !== toggleBtn) panel.classList.remove('active');
  });

  // Crear guía de lectura
  let guia = document.querySelector('.reading-guide-mask');
  if (!guia) {
    guia = document.createElement('div');
    guia.className = 'reading-guide-mask';
    document.body.appendChild(guia);
  }

  // Funciones para guardar/cargar estado
  const saveState = (key, value) => localStorage.setItem(key, value);
  const loadState = key => localStorage.getItem(key) === 'true';

  // Inicializar estados guardados
  if (loadState('lightMode')) {
    document.body.classList.add('light-mode');
    document.getElementById('toggle-dark').innerText = 'Modo Oscuro';
  } else {
    document.body.classList.add('dark-mode');
    document.getElementById('toggle-dark').innerText = 'Modo Claro';
  }
  if (loadState('highContrast')) document.body.classList.add('high-contrast');
  if (loadState('largeText')) document.body.classList.add('large-text');
  if (loadState('altFont')) document.body.classList.add('alt-font');
  if (loadState('grayscale')) document.body.classList.add('grayscale');
  if (loadState('readingGuide')) {
    document.body.classList.add('reading-guide-active');
    guia.style.display = 'block';
  }

  // Toggle modo oscuro/diurno
  const darkBtn = document.getElementById('toggle-dark');
  darkBtn.addEventListener('click', () => {
    if (document.body.classList.contains('dark-mode')) {
      document.body.classList.remove('dark-mode');
      document.body.classList.add('light-mode');
      darkBtn.innerText = 'Modo Oscuro';
      saveState('lightMode', true);
    } else {
      document.body.classList.remove('light-mode');
      document.body.classList.add('dark-mode');
      darkBtn.innerText = 'Modo Claro';
      saveState('lightMode', false);
    }
  });

  // Función genérica para otros toggles
  const toggleClass = (btnId, className, storageKey) => {
    const btn = document.getElementById(btnId);
    btn.addEventListener('click', () => {
      document.body.classList.toggle(className);
      saveState(storageKey, document.body.classList.contains(className));

      if (storageKey === 'readingGuide') {
        guia.style.display = document.body.classList.contains(className) ? 'block' : 'none';
      }
    });
  };

  toggleClass('toggle-contrast', 'high-contrast', 'highContrast');
  toggleClass('toggle-font', 'alt-font', 'altFont');
  toggleClass('toggle-size', 'large-text', 'largeText');
  toggleClass('toggle-grayscale', 'grayscale', 'grayscale');
  toggleClass('toggle-guide', 'reading-guide-active', 'readingGuide');

  // Movimiento de la guía de lectura
  document.addEventListener('mousemove', e => {
    if (document.body.classList.contains('reading-guide-active')) {
      guia.style.top = `${e.clientY - 20}px`;
    }
  });

  // Lectura en voz alta
  const readBtn = document.getElementById('toggle-read');
  let lecturaActiva = false;
  readBtn.addEventListener('click', () => {
    if (!('speechSynthesis' in window)) return alert("Tu navegador no soporta lectura de texto.");
    if (!lecturaActiva) {
      const utterance = new SpeechSynthesisUtterance(document.body.innerText);
      utterance.lang = 'es-ES';
      utterance.rate = 1;
      speechSynthesis.speak(utterance);
      lecturaActiva = true;
      readBtn.innerText = 'Detener lectura';
      utterance.onend = () => { lecturaActiva = false; readBtn.innerText = 'Lectura en voz alta'; };
    } else {
      speechSynthesis.cancel();
      lecturaActiva = false;
      readBtn.innerText = 'Lectura en voz alta';
    }
  });
});
