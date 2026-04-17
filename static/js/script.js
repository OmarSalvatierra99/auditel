// static/script.js - VERSIÓN MEJORADA CON MARKDOWN Y BÚSQUEDA EN INTERNET
document.addEventListener("DOMContentLoaded", function() {
    // === CONFIGURACIÓN INICIAL ===
    const askForm = document.getElementById("ask-form");
    const chatBox = document.getElementById("chat-box");
    const welcomeMessage = document.querySelector(".welcome-message");
    const questionTextarea = askForm.querySelector('textarea[name="question"]');
    const sendButton = askForm.querySelector('.send-button');

    // Estado mejorado de la conversación
    const conversationState = {
        auditoria: null,
        ente: null,
        configuracionCompleta: false,
        isProcessing: false,
        messageCount: 0,
        lastActivity: Date.now()
    };

    // === SISTEMA DE REINTENTOS INTELIGENTE ===
    class SistemaReintentos {
        constructor(maxReintentos = 2, delayBase = 1000) {
            this.maxReintentos = maxReintentos;
            this.delayBase = delayBase;
        }

        async ejecutarConReintento(operacion, descripcion) {
            let ultimoError;
            
            for (let intento = 1; intento <= this.maxReintentos + 1; intento++) {
                try {
                    if (intento > 1) {
                        console.log(`🔄 Reintento ${intento-1}/${this.maxReintentos} para: ${descripcion}`);
                        await this.delay(this.delayBase * Math.pow(2, intento - 2));
                    }
                    
                    return await operacion();
                } catch (error) {
                    ultimoError = error;
                    console.warn(`Intento ${intento} falló:`, error);
                    
                    if (intento > this.maxReintentos) {
                        break;
                    }
                }
            }
            
            throw ultimoError;
        }

        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    }

    const reintentos = new SistemaReintentos();

    // === INICIALIZACIÓN MEJORADA ===
    function inicializarAplicacion() {
        configurarMarkdown();
        inicializarFormulario();
        inicializarEventos();
        inicializarValidacionTiempoReal();
        inicializarDeteccionInactividad();
        startConversation();
    }

    function configurarMarkdown() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: false,
                headerIds: true,
                highlight: function(code, lang) {
                    return code;
                }
            });
        }
    }

    function inicializarFormulario() {
        questionTextarea.style.display = 'none';
        sendButton.style.display = 'none';
        questionTextarea.disabled = true;
        sendButton.disabled = true;
        questionTextarea.value = '';

        questionTextarea.style.height = '50px';
        questionTextarea.style.minHeight = '50px';
        questionTextarea.style.maxHeight = '120px';
    }

    function inicializarEventos() {
        questionTextarea.addEventListener('input', function() {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120);
            this.style.height = newHeight + 'px';
        });

        questionTextarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim() && !conversationState.isProcessing) {
                    enviarPregunta();
                }
            }

            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                if (this.value.trim() && !conversationState.isProcessing) {
                    enviarPregunta();
                }
            }
        });

        questionTextarea.addEventListener('input', function() {
            const tieneTexto = this.value.trim().length > 0;
            sendButton.disabled = !tieneTexto || conversationState.isProcessing;
            actualizarContadorCaracteres(this.value.length);
        });

        // Eventos de actividad del usuario
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        events.forEach(event => {
            document.addEventListener(event, () => {
                conversationState.lastActivity = Date.now();
            }, false);
        });
    }

    function inicializarValidacionTiempoReal() {
        const contador = document.createElement('div');
        contador.className = 'character-counter';
        contador.textContent = '0/2000';
        questionTextarea.parentNode.appendChild(contador);
    }

    function inicializarDeteccionInactividad() {
        setInterval(() => {
            const tiempoInactivo = Date.now() - conversationState.lastActivity;
            if (tiempoInactivo > 10 * 60 * 1000 && !conversationState.isProcessing) { // 10 minutos
                mostrarAdvertenciaInactividad();
            }
        }, 60000); // Verificar cada minuto
    }

    function mostrarAdvertenciaInactividad() {
        const advertencia = showBotMessage(`
            <div class="inactivity-warning">
                <p>⏰ <strong>Sesión inactiva</strong></p>
                <p>Tu sesión se cerrará automáticamente por inactividad.</p>
                <p><small>Realiza una acción para mantener la sesión activa.</small></p>
            </div>
        `, null, true);
    }

    function actualizarContadorCaracteres(longitud) {
        const contador = document.querySelector('.character-counter');
        if (contador) {
            contador.textContent = `${longitud}/2000`;
            
            if (longitud > 1800) {
                contador.style.color = '#ff6b6b';
            } else if (longitud > 1500) {
                contador.style.color = '#ffa500';
            } else {
                contador.style.color = '#666';
            }
        }
    }

    // === MANEJO DE MENSAJES MEJORADO ===
    function normalizeMultilineText(text) {
        if (typeof text !== 'string') {
            return text;
        }

        const lines = text.replace(/\r\n/g, '\n').split('\n');
        let minIndent = Infinity;

        for (const line of lines) {
            if (!line.trim()) {
                continue;
            }

            const indent = line.match(/^\s*/)[0].length;
            if (indent < minIndent) {
                minIndent = indent;
            }
        }

        if (!isFinite(minIndent)) {
            return text.trim();
        }

        return lines
            .map(line => line.trim() ? line.slice(minIndent) : '')
            .join('\n')
            .trim();
    }

    function showBotMessage(messageHtml, context = null, isMarkdown = false) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.className = "chat-message bot";

        const timestamp = new Date().toLocaleTimeString('es-MX', {
            hour: '2-digit',
            minute: '2-digit'
        });

        let contenidoHTML = normalizeMultilineText(messageHtml);
        
        // ✅ CORRECCIÓN: Procesar Markdown solo si es necesario
        if (isMarkdown && typeof marked !== 'undefined') {
            try {
                contenidoHTML = marked.parse(contenidoHTML);
            } catch (error) {
                console.error('Error procesando markdown:', error);
                contenidoHTML = normalizeMultilineText(messageHtml);
            }
        }

        botMessageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-avatar">🔍</span>
                <span class="message-sender">Auditel</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${contenidoHTML}</div>
            ${context ? `<div class="message-context">${context}</div>` : ''}
        `;

        chatBox.appendChild(botMessageDiv);
        scrollToBottom();
        return botMessageDiv;
    }

    function showUserMessage(messageText) {
        const userMessageDiv = document.createElement("div");
        userMessageDiv.className = "chat-message user";

        const timestamp = new Date().toLocaleTimeString('es-MX', {
            hour: '2-digit',
            minute: '2-digit'
        });

        userMessageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-avatar">👤</span>
                <span class="message-sender">Tú</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${escapeHtml(messageText)}</div>
        `;

        chatBox.appendChild(userMessageDiv);
        scrollToBottom();
        conversationState.messageCount++;
        conversationState.lastActivity = Date.now();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // === SISTEMA DE SELECCIÓN MEJORADO ===
    function createSelectionButtons(options, onSelectCallback, compact = false) {
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = `selection-buttons ${compact ? 'compact' : ''}`;

        options.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = option.text;
            button.setAttribute('data-value', option.value);
            button.setAttribute('aria-label', option.text);

            button.addEventListener('click', (e) => {
                e.preventDefault();
                buttonsContainer.querySelectorAll('button').forEach(btn => {
                    btn.disabled = true;
                    btn.style.opacity = '0.6';
                });
                button.style.borderColor = 'var(--accent-color)';
                button.style.background = 'rgba(0, 255, 200, 0.1)';
                onSelectCallback(option.value, option.text);
            });

            buttonsContainer.appendChild(button);
        });

        return buttonsContainer;
    }

    // === FLUJO DE CONVERSACIÓN MEJORADO ===
    function handleAuditoriaSelection(value, text) {
        showUserMessage(`Tipo de auditoría: ${text}`);
        conversationState.auditoria = value;

        const descripciones = {
            'Obra Pública': 'Análisis de normativas de construcción, licitaciones y contratación pública',
            'Financiera': 'Análisis de normativas contables, presupuestales y de control financiero'
        };

        if (value === 'Financiera') {
            const entePrompt = showBotMessage(`
                <p>💰 <strong>Auditoría Financiera seleccionada</strong></p>
                <p>${descripciones[value]}</p>
                <p>Para brindarte respuestas más precisas, selecciona el tipo de ente:</p>
            `, null, false);

            const enteButtons = createSelectionButtons(
                [
                    { text: '🏛️ Ente Autónomo', value: 'Autónomo' },
                    { text: '🏢 Paraestatal/Descentralizada', value: 'Paraestatal' },
                    { text: '📊 Centralizada', value: 'Centralizada' },
                    { text: '❓ No especificar', value: 'No especificado' }
                ],
                handleEnteSelection
            );
            entePrompt.appendChild(enteButtons);
        } else {
            conversationState.ente = 'No aplica';
            showQuestionForm(descripciones[value]);
        }
    }

    function handleEnteSelection(value, text) {
        showUserMessage(`Tipo de ente: ${text}`);
        conversationState.ente = value;

        const descripcion = conversationState.auditoria === 'Financiera'
            ? 'Análisis de normativas contables, presupuestales y de control financiero'
            : 'Análisis de normativas de construcción, licitaciones y contratación pública';

        showQuestionForm(descripcion);
    }

    function showQuestionForm(descripcion) {
        conversationState.configuracionCompleta = true;

        showBotMessage(`
            <div class="detection-badge">
                ✅ <strong>¡Configuración completada!</strong>
            </div>
            <p>Ahora puedo ayudarte con <strong>análisis normativo automático</strong>:</p>
            <ul>
                <li>⚖️ <strong>Detección automática</strong> de normativas aplicables</li>
                <li>📋 <strong>Listado estructurado</strong> de regulaciones relevantes</li>
                <li>🔍 <strong>Búsqueda inteligente</strong> en base de datos normativa</li>
                <li>🌐 <strong>Búsqueda en internet</strong> de normativas actualizadas</li>
                <li>🎯 <strong>Especializado en:</strong> ${descripcion}</li>
            </ul>
            <div class="context-info">
                <strong>Contexto configurado:</strong><br>
                🏛️ <strong>Auditoría:</strong> ${conversationState.auditoria}<br>
                ${conversationState.ente ? `📋 <strong>Ente:</strong> ${conversationState.ente}` : ''}
            </div>
            <p>Escribe tu consulta y analizaré automáticamente las normativas aplicables.</p>
        `, null, false);

        questionTextarea.style.display = 'block';
        sendButton.style.display = 'flex';
        questionTextarea.disabled = false;
        sendButton.disabled = true;
        questionTextarea.focus();
    }

    // === BÚSQUEDA EN INTERNET MEJORADA ===
    function generarEnlacesBusqueda(consulta, auditoria) {
        const consultaCodificada = encodeURIComponent(consulta + ' ' + auditoria + ' normativa México');

        const enlaces = {
            'DOF - Diario Oficial de la Federación': `https://www.dof.gob.mx/busqueda_avanzada.php?q=${consultaCodificada}`,
            'Cámara de Diputados - Leyes Federales': `http://www.diputados.gob.mx/LeyesBiblio/index.htm`,
            'SCJN - Suprema Corte de Justicia': `https://www.scjn.gob.mx/busqueda?search=${consultaCodificada}`,
            'Google - Búsqueda General': `https://www.google.com/search?q=${consultaCodificada}`
        };

        let html = '<div class="internet-search">';
        html += '<h4>🔍 Búsquedas Sugeridas en Internet</h4>';
        html += '<p>Para información más actualizada, puedes consultar estas fuentes oficiales:</p>';
        html += '<div class="search-links">';

        for (const [nombre, url] of Object.entries(enlaces)) {
            html += `<a href="${url}" target="_blank" rel="noopener noreferrer" class="search-link">
                        <span class="search-icon">🌐</span>
                        <span>${nombre}</span>
                     </a>`;
        }

        html += '</div>';
        html += '<p class="search-note">💡 <em>Estos enlaces te llevarán a fuentes oficiales para verificar la normativa más actualizada</em></p>';
        html += '</div>';

        return html;
    }

    // === MANEJO DE ENVÍO MEJORADO ===
    function enviarPregunta() {
        const question = questionTextarea.value.trim();

        if (!question || conversationState.isProcessing) {
            return;
        }

        // Validación mejorada
        const errores = validarContenidoTiempoReal(question);
        if (errores.length > 0) {
            showBotMessage(`
                <div class="validation-error">
                    <p>❌ <strong>Problemas con tu consulta:</strong></p>
                    <ul>
                        ${errores.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            `, null, true);
            return;
        }

        showUserMessage(question);
        conversationState.isProcessing = true;
        setUIProcessingState(true);

        const loadingMessageDiv = showBotMessage(`
            <div class="loading-message">
                <p>🔍 <strong>Analizando normativas aplicables...</strong></p>
                <div class="loading-spinner"></div>
                <p><small>Buscando regulaciones relevantes en ${conversationState.auditoria}</small></p>
                <p><small>Consultando bases de datos y generando enlaces de búsqueda</small></p>
            </div>
        `, null, false);

        enviarSolicitudAnalisis(question, loadingMessageDiv);
    }

    function validarContenidoTiempoReal(texto) {
        const errores = [];
        
        if (texto.length < 3) {
            errores.push('La consulta es muy corta (mínimo 3 caracteres)');
        }
        
        if (texto.length > 2000) {
            errores.push('La consulta es demasiado larga (máximo 2000 caracteres)');
        }
        
        // Detectar preguntas demasiado genéricas
        const palabras = texto.toLowerCase().split(/\s+/);
        const palabrasGenericas = ['qué', 'como', 'cuando', 'donde', 'quien', 'cuales', 'que', 'como'];
        const palabrasGenericasCount = palabras.filter(p => palabrasGenericas.includes(p)).length;
        
        if (palabrasGenericasCount > 2 && palabras.length < 10) {
            errores.push('Consulta muy genérica. Sé más específico para mejores resultados.');
        }
        
        return errores;
    }

    function setUIProcessingState(processing) {
        conversationState.isProcessing = processing;
        questionTextarea.disabled = processing;
        sendButton.disabled = processing || !questionTextarea.value.trim();

        if (processing) {
            sendButton.innerHTML = '⏳';
            sendButton.classList.add('loading');
        } else {
            sendButton.innerHTML = '➤';
            sendButton.classList.remove('loading');
        }
    }

    async function enviarSolicitudAnalisis(question, loadingMessageDiv) {
        const formData = new FormData();
        formData.append("question", question);
        formData.append("auditoria", conversationState.auditoria);
        formData.append("ente", conversationState.ente || "No especificado");

        try {
            const respuesta = await reintentos.ejecutarConReintento(
                () => fetchConTimeout("/ask", {
                    method: "POST",
                    body: formData,
                    timeout: 45000 // 45 segundos
                }),
                "análisis normativo"
            );
            
            await procesarRespuestaMejorada(respuesta, loadingMessageDiv, question);
        } catch (error) {
            manejarErrorMejorado(error, loadingMessageDiv, question);
        } finally {
            finalizarProcesamiento();
        }
    }

    async function fetchConTimeout(url, options = {}) {
        const { timeout = 45000, ...fetchOptions } = options;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                ...fetchOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    async function procesarRespuestaMejorada(response, loadingMessageDiv, preguntaOriginal) {
        const data = await response.json();
        loadingMessageDiv.remove();

        if (data.success) {
            const context = `Contexto: ${conversationState.auditoria} • ${conversationState.ente || 'No aplica'} • Normativas encontradas: ${data.normativas_encontradas} • Tiempo: ${data.tiempo_procesamiento}`;

            let respuestaCompleta = data.answer;

            // ✅ AGREGAR BÚSQUEDA EN INTERNET SI HAY POCOS RESULTADOS
            if (data.normativas_encontradas < 3) {
                respuestaCompleta += generarEnlacesBusqueda(preguntaOriginal, conversationState.auditoria);
            } else {
                // Agregar enlaces de referencia incluso con buenos resultados
                respuestaCompleta += `
                    <div class="internet-search">
                        <p><strong>🔍 ¿Necesitas más información?</strong></p>
                        <p>Puedes consultar estas fuentes oficiales para normativas actualizadas:</p>
                        ${generarEnlacesBusqueda(preguntaOriginal, conversationState.auditoria)}
                    </div>
                `;
            }

            showBotMessage(respuestaCompleta, context, true);

        } else {
            let mensajeError = `
                <div class="error-message">
                    <p>❌ <strong>Error en el análisis</strong></p>
                    <p>${data.message || 'Error desconocido al procesar tu consulta.'}</p>
                    <p><small>Por favor, intenta nuevamente o reformula tu pregunta.</small></p>
                </div>
            `;

            mensajeError += generarEnlacesBusqueda(preguntaOriginal, conversationState.auditoria);

            showBotMessage(mensajeError, null, true);
        }
    }

    function manejarErrorMejorado(error, loadingMessageDiv, preguntaOriginal) {
        loadingMessageDiv.remove();

        let mensajeError = '';
        if (error.name === 'AbortError') {
            mensajeError = `
                <div class="error-message">
                    <p>⏰ <strong>Tiempo de espera agotado</strong></p>
                    <p>El análisis está tomando más tiempo de lo esperado.</p>
                    <p><small>Puedes intentar con una consulta más específica o usar los enlaces de búsqueda directa.</small></p>
                </div>
            `;
        } else if (error.message.includes('servidor') || error.message.includes('HTTP 5')) {
            mensajeError = `
                <div class="error-message">
                    <p>🔧 <strong>Error del servidor</strong></p>
                    <p>Estamos experimentando problemas técnicos.</p>
                    <p><small>Puedes usar los enlaces de búsqueda directa mientras resolvemos el problema.</small></p>
                </div>
            `;
        } else if (error.message.includes('HTTP 4')) {
            mensajeError = `
                <div class="error-message">
                    <p>📝 <strong>Error en la solicitud</strong></p>
                    <p>Verifica que tu consulta esté bien formulada.</p>
                    <p><small>Intenta reformular tu pregunta o verifica la conexión.</small></p>
                </div>
            `;
        } else {
            mensajeError = `
                <div class="error-message">
                    <p>🌐 <strong>Error de conexión</strong></p>
                    <p>Verifica tu conexión a internet e intenta nuevamente.</p>
                    <p><small>Si el problema persiste, contacta al administrador.</small></p>
                </div>
            `;
        }

        mensajeError += generarEnlacesBusqueda(preguntaOriginal, conversationState.auditoria);

        showBotMessage(mensajeError, null, true);
        console.error('Error en análisis normativo:', error);
    }

    function finalizarProcesamiento() {
        setUIProcessingState(false);
        questionTextarea.value = "";
        questionTextarea.style.height = '50px';
        actualizarContadorCaracteres(0);
        questionTextarea.focus();
        scrollToBottom();
    }

    // === UTILIDADES MEJORADAS ===
    function scrollToBottom() {
        setTimeout(() => {
            chatBox.scrollTo({
                top: chatBox.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    function startConversation() {
        if (welcomeMessage) {
            welcomeMessage.style.display = "none";
        }

        const disclaimer = document.querySelector('.disclaimer-message');
        if (disclaimer) {
            disclaimer.style.display = 'block';
        }

        // ✅ CORRECCIÓN: Mensaje de bienvenida con HTML directo (sin markdown)
        const auditoriaPrompt = showBotMessage(`
            <div class="welcome-header">
                <h3>👋 ¡Hola! Soy <strong>Auditel</strong></h3>
                <p>Tu asistente especializado en <strong>análisis normativo de auditoría</strong></p>
            </div>
            <p>Para realizar un análisis preciso de las normativas aplicables, por favor selecciona el tipo de auditoría:</p>
        `, null, false);

        const auditoriaButtons = createSelectionButtons(
            [
                { text: '🏗️ Obra Pública', value: 'Obra Pública' },
                { text: '💰 Financiera', value: 'Financiera' }
            ],
            handleAuditoriaSelection
        );
        auditoriaPrompt.appendChild(auditoriaButtons);
    }

    // === EVENTOS GLOBALES ===
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && conversationState.configuracionCompleta && !conversationState.isProcessing) {
            questionTextarea.focus();
        }
    });

    // Prevenir navegación accidental durante el procesamiento
    window.addEventListener('beforeunload', function(e) {
        if (conversationState.isProcessing) {
            e.preventDefault();
            e.returnValue = 'Hay una consulta en proceso. ¿Estás seguro de que quieres salir?';
            return e.returnValue;
        }
    });

    // Inicializar la aplicación
    inicializarAplicacion();

    // === CONSOLA DE DESARROLLO ===
    console.log('🔍 Auditel v2.1 inicializado correctamente');
    console.log('📊 Configuración:', window.auditelConfig || 'No disponible');
});
