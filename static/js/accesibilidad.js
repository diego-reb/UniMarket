document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.createElement('button');
  toggleBtn.id = 'accesibility-toggle';
  toggleBtn.title = 'Opciones de accesibilidad';
  toggleBtn.innerHTML = '♿';
  document.body.appendChild(toggleBtn);

  const panel = document.createElement('div');
  panel.id = 'accesibility-panel';
  panel.innerHTML = `
    <button id="toggle-dark">Modo Oscuro / Claro</button>
    <button id="toggle-contrast">Alto contraste</button>
    <button id="toggle-font">Tipografía accesible</button>
    <button id="toggle-size">Aumentar tamaño</button>
    <button id="toggle-grayscale">Escala de grises</button>
    <button id="toggle-guide">Guía de lectura</button>
  `;
  document.body.appendChild(panel);

  // Mostrar/Ocultar panel
  toggleBtn.addEventListener('click', () => panel.classList.toggle('active'));
  document.addEventListener('click', e => {
    if (!panel.contains(e.target) && e.target !== toggleBtn) {
      panel.classList.remove('active');
    }
  });

  // Crear guía si no existe
  let guia = document.querySelector('.reading-guide-mask');
  if (!guia) {
    guia = document.createElement('div');
    guia.className = 'reading-guide-mask';
    document.body.appendChild(guia);
  }

  // Funciones de guardado
  const saveState = (key, value) => localStorage.setItem(key, value);
  const loadState = key => localStorage.getItem(key) === 'true';

  // Cargar estados
  if (loadState('darkMode')) document.body.classList.add('dark-mode');
  if (loadState('lightMode')) document.body.classList.add('light-mode');
  if (loadState('highContrast')) document.body.classList.add('high-contrast');
  if (loadState('largeText')) document.body.classList.add('large-text');
  if (loadState('altFont')) document.body.classList.add('alt-font');
  if (loadState('grayscale')) document.body.classList.add('grayscale');
  if (loadState('readingGuide')) {
    document.body.classList.add('reading-guide-active');
    guia.style.display = 'block';
  }

  // Alternar Dark/Light
  document.getElementById('toggle-dark').addEventListener('click', () => {
    if (document.body.classList.contains('dark-mode')) {
      document.body.classList.remove('dark-mode');
      document.body.classList.add('light-mode');
      saveState('darkMode', false);
      saveState('lightMode', true);
    } else {
      document.body.classList.remove('light-mode');
      document.body.classList.add('dark-mode');
      saveState('darkMode', true);
      saveState('lightMode', false);
    }
  });

  // Otras opciones
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

  // Movimiento de guía
  document.addEventListener('mousemove', e => {
    if (document.body.classList.contains('reading-guide-active')) {
      guia.style.top = `${e.clientY - 20}px`;
    }
  });
});
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.createElement('button');
  toggleBtn.id = 'accesibility-toggle';
  toggleBtn.title = 'Opciones de accesibilidad';
  toggleBtn.innerHTML = '♿';
  document.body.appendChild(toggleBtn);

  const panel = document.createElement('div');
  panel.id = 'accesibility-panel';
  panel.innerHTML = `
    <button id="toggle-dark">Modo Oscuro / Claro</button>
    <button id="toggle-contrast">Alto contraste</button>
    <button id="toggle-font">Tipografía accesible</button>
    <button id="toggle-size">Aumentar tamaño</button>
    <button id="toggle-grayscale">Escala de grises</button>
    <button id="toggle-guide">Guía de lectura</button>
    <button id="toggle-read">Lectura en voz alta</button>
  `;
  document.body.appendChild(panel);

  toggleBtn.addEventListener('click', () => panel.classList.toggle('active'));
  document.addEventListener('click', e => {
    if (!panel.contains(e.target) && e.target !== toggleBtn) {
      panel.classList.remove('active');
    }
  });

  let guia = document.querySelector('.reading-guide-mask');
  if (!guia) {
    guia = document.createElement('div');
    guia.className = 'reading-guide-mask';
    document.body.appendChild(guia);
  }

  
  const saveState = (key, value) => localStorage.setItem(key, value);
  const loadState = key => localStorage.getItem(key) === 'true';

  if (loadState('darkMode')) document.body.classList.add('dark-mode');
  if (loadState('lightMode')) document.body.classList.add('light-mode');
  if (loadState('highContrast')) document.body.classList.add('high-contrast');
  if (loadState('largeText')) document.body.classList.add('large-text');
  if (loadState('altFont')) document.body.classList.add('alt-font');
  if (loadState('grayscale')) document.body.classList.add('grayscale');
  if (loadState('readingGuide')) {
    document.body.classList.add('reading-guide-active');
    guia.style.display = 'block';
  }

  document.getElementById('toggle-dark').addEventListener('click', () => {
    if (document.body.classList.contains('dark-mode')) {
      document.body.classList.remove('dark-mode');
      document.body.classList.add('light-mode');
      saveState('darkMode', false);
      saveState('lightMode', true);
    } else {
      document.body.classList.remove('light-mode');
      document.body.classList.add('dark-mode');
      saveState('darkMode', true);
      saveState('lightMode', false);
    }
  });

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

  document.addEventListener('mousemove', e => {
    if (document.body.classList.contains('reading-guide-active')) {
      guia.style.top = `${e.clientY - 20}px`;
    }
  });
  let lecturaActiva = false;
    const readBtn = document.getElementById('toggle-read');
    readBtn.addEventListener('click', () => {
        if (!('speechSynthesis' in window)) {
            alert("Tu navegador no soporta lectura de texto.");
            return;
        }

        if (!lecturaActiva) {
            const utterance = new SpeechSynthesisUtterance(document.body.innerText);
            utterance.lang = 'es-ES';
            utterance.rate = 1;
            speechSynthesis.speak(utterance);
            lecturaActiva = true;
            readBtn.innerText = 'Detener lectura';

            utterance.onend = () => {
                lecturaActiva = false;
                readBtn.innerText = 'Lectura en voz alta';
            };
        } else {
            speechSynthesis.cancel();
            lecturaActiva = false;
            readBtn.innerText = 'Lectura en voz alta';
        }
    });
});