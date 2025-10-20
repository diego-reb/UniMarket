document.addEventListener('DOMContentLoaded', () => {

    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'accesibility-toggle';
    toggleBtn.title = 'Opciones de accesibilidad';
    toggleBtn.innerHTML = '♿';
    document.body.appendChild(toggleBtn);

    
    const panel = document.createElement('div');
    panel.id = 'accesibility-panel';
    panel.innerHTML = `
        <button id="toggle-dark">Modo Oscuro/Claro</button>
        <button id="toggle-guide">Guía de lectura</button>

        <button id="toggle-font">Tipografía accesible</button>
        <button id="toggle-grayscale">Escala de grises</button>
        
    `;
    document.body.appendChild(panel);

    toggleBtn.addEventListener('click', () => panel.classList.toggle('active'));
    document.addEventListener('click', e => {
        if (!panel.contains(e.target) && e.target !== toggleBtn) {
            panel.classList.remove('active');
        }
    });

    
    const guia = document.getElementById('reading-guide');
    const saveState = (key, value) => localStorage.setItem(key, value);
    const loadState = key => localStorage.getItem(key) === 'true';

    
    
    if (loadState('altFont')) document.body.classList.add('alt-font');
    if (loadState('grayscale')) document.body.classList.add('grayscale');
    if (loadState('darkMode')) document.body.classList.add('dark-mode');
    if (loadState('lightMode')) document.body.classList.add('light-mode');

    if (loadState('readingGuide')) {
        document.body.classList.add('reading-guide-active');
        guia.style.display = 'block';
    }
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
    
    toggleClass('toggle-guide', 'reading-guide-active', 'readingGuide');
    toggleClass('toggle-dark', 'dark-mode', 'darkMode');
    toggleClass('toggle-dark', 'light-mode', 'lightMode');
    toggleClass('toggle-grayscale', 'grayscale', 'grayscale');
    
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
