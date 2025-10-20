document.addEventListener('DOMContentLoaded', () => {

    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'accesibility-toggle';
    toggleBtn.title = 'Opciones de accesibilidad';
    toggleBtn.innerHTML = '♿';
    document.body.appendChild(toggleBtn);

    
    const panel = document.createElement('div');
    panel.id = 'accesibility-panel';
    panel.innerHTML = `
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

    

    const saveState = (key, value) => localStorage.setItem(key, value);
    const loadState = key => localStorage.getItem(key) === 'true';

    
    
    if (loadState('altFont')) document.body.classList.add('alt-font');
    if (loadState('grayscale')) document.body.classList.add('grayscale');
    

    

    
    
    toggleClass('toggle-grayscale', 'grayscale', 'grayscale');
    

    

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
