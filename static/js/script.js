document.addEventListener("DOMContentLoaded", function () {
    const askForm = document.getElementById("ask-form");
    if (!askForm) {
        return;
    }

    const chatBox = document.getElementById("chat-box");
    const questionTextarea = askForm.querySelector('textarea[name="question"]');
    const sendButton = askForm.querySelector(".send-button");
    const welcomeMessage = chatBox.querySelector(".welcome-message");
    const hiddenAuditoria = askForm.querySelector('input[name="auditoria"]');
    const hiddenEnte = askForm.querySelector('input[name="ente"]');
    const slashMenu = askForm.querySelector("#chatbot-slash-menu");
    const contextChip = askForm.querySelector("#chatbot-context-chip");
    const contextValue = askForm.querySelector("#chatbot-context-value");
    const clearContextButton = askForm.querySelector("#chatbot-context-clear");
    const chatbotConfig = window.chatbotConfig || {};
    const botName = chatbotConfig.botName || "Chatbot";
    const slashCommands = Array.isArray(chatbotConfig.slashCommands) ? chatbotConfig.slashCommands : [];

    const state = {
        isProcessing: false,
        slashMenuOpen: false,
        slashQuery: "",
        slashIndex: 0,
        selectedAuditoria: hiddenAuditoria?.value || chatbotConfig.defaultAuditoria || "auto",
    };

    inicializar();

    function inicializar() {
        configurarEventos();
        crearContadorCaracteres();
        actualizarEstadoEnvio();
        ajustarAlturaTextarea();
        renderizarContextoActivo();
        scrollToBottom("auto");

        if (questionTextarea) {
            questionTextarea.focus();
        }
    }

    function configurarEventos() {
        askForm.addEventListener("submit", function (event) {
            event.preventDefault();

            if (!state.isProcessing) {
                enviarPregunta();
            }
        });

        questionTextarea.addEventListener("input", function () {
            ajustarAlturaTextarea();
            actualizarContadorCaracteres(this.value.length);
            actualizarSlashCommands();
            actualizarEstadoEnvio();
        });

        questionTextarea.addEventListener("keydown", function (event) {
            if (state.slashMenuOpen) {
                if (event.key === "ArrowDown") {
                    event.preventDefault();
                    moverSlashIndex(1);
                    return;
                }

                if (event.key === "ArrowUp") {
                    event.preventDefault();
                    moverSlashIndex(-1);
                    return;
                }

                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    seleccionarSlashActivo();
                    return;
                }

                if (event.key === "Escape") {
                    cerrarSlashMenu();
                    return;
                }
            }

            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                if (!state.isProcessing && this.value.trim()) {
                    enviarPregunta();
                }
            }
        });

        clearContextButton?.addEventListener("click", function () {
            aplicarContextoAuditoria(chatbotConfig.defaultAuditoria || "auto");
            questionTextarea.focus();
        });

        slashMenu?.addEventListener("click", function (event) {
            const option = event.target.closest(".chatbot-slash-option");
            if (!option) {
                return;
            }

            aplicarSlashCommand(option.dataset.value);
        });

        document.addEventListener("click", function (event) {
            if (!state.slashMenuOpen) {
                return;
            }

            if (askForm.contains(event.target)) {
                return;
            }

            cerrarSlashMenu();
        });

        document.addEventListener("visibilitychange", function () {
            if (!document.hidden && questionTextarea && !state.isProcessing) {
                questionTextarea.focus();
            }
        });

        window.addEventListener("beforeunload", function (event) {
            if (!state.isProcessing) {
                return;
            }

            event.preventDefault();
            event.returnValue = "Hay una consulta en proceso.";
            return event.returnValue;
        });
    }

    function crearContadorCaracteres() {
        if (askForm.querySelector(".character-counter")) {
            return;
        }

        const counter = document.createElement("div");
        counter.className = "character-counter";
        counter.textContent = `0/${chatbotConfig.maxQuestionLength || 2000}`;
        askForm.appendChild(counter);
    }

    function actualizarContadorCaracteres(length) {
        const counter = askForm.querySelector(".character-counter");
        if (!counter) {
            return;
        }

        const maxLength = chatbotConfig.maxQuestionLength || 2000;
        counter.textContent = `${length}/${maxLength}`;

        if (length > maxLength * 0.9) {
            counter.classList.add("is-warning");
        } else {
            counter.classList.remove("is-warning");
        }
    }

    function ajustarAlturaTextarea() {
        questionTextarea.style.height = "auto";
        questionTextarea.style.height = `${Math.min(questionTextarea.scrollHeight, 180)}px`;
    }

    function actualizarEstadoEnvio() {
        const hasText = Boolean(questionTextarea.value.trim());
        sendButton.disabled = state.isProcessing || !hasText;
    }

    function getSlashCommandsFiltrados() {
        const query = (state.slashQuery || "").trim().toLowerCase();
        if (!query) {
            return slashCommands;
        }

        return slashCommands.filter(function (command) {
            return [command.label, command.value, command.description].some(function (part) {
                return typeof part === "string" && part.toLowerCase().includes(query);
            });
        });
    }

    function getSlashTriggerMatch() {
        const cursorPosition = questionTextarea.selectionStart || 0;
        const textBeforeCursor = questionTextarea.value.slice(0, cursorPosition);
        return textBeforeCursor.match(/(^|\s)\/([^\s/]*)$/);
    }

    function actualizarSlashCommands() {
        const match = getSlashTriggerMatch();
        if (!match) {
            cerrarSlashMenu();
            return;
        }

        state.slashQuery = match[2] || "";
        const commands = getSlashCommandsFiltrados();
        if (!commands.length) {
            cerrarSlashMenu();
            return;
        }

        state.slashMenuOpen = true;
        state.slashIndex = Math.min(state.slashIndex, commands.length - 1);
        renderizarSlashMenu(commands);
    }

    function renderizarSlashMenu(commands) {
        if (!slashMenu) {
            return;
        }

        slashMenu.hidden = false;
        slashMenu.innerHTML = commands.map(function (command, index) {
            const isActive = index === state.slashIndex;
            return `
                <button
                    type="button"
                    class="chatbot-slash-option ${isActive ? "is-active" : ""}"
                    data-value="${escapeHtml(command.value)}"
                >
                    <strong>/${escapeHtml(command.label)}</strong>
                    <span>${escapeHtml(command.description || "")}</span>
                </button>
            `;
        }).join("");
    }

    function cerrarSlashMenu() {
        state.slashMenuOpen = false;
        state.slashQuery = "";
        state.slashIndex = 0;
        if (slashMenu) {
            slashMenu.hidden = true;
            slashMenu.innerHTML = "";
        }
    }

    function moverSlashIndex(direction) {
        const commands = getSlashCommandsFiltrados();
        if (!commands.length) {
            return;
        }

        state.slashIndex = (state.slashIndex + direction + commands.length) % commands.length;
        renderizarSlashMenu(commands);
    }

    function seleccionarSlashActivo() {
        const commands = getSlashCommandsFiltrados();
        const activeCommand = commands[state.slashIndex];
        if (!activeCommand) {
            return;
        }

        aplicarSlashCommand(activeCommand.value);
    }

    function aplicarSlashCommand(commandValue) {
        const cursorPosition = questionTextarea.selectionStart || 0;
        const textBeforeCursor = questionTextarea.value.slice(0, cursorPosition);
        const textAfterCursor = questionTextarea.value.slice(cursorPosition);
        const updatedBeforeCursor = textBeforeCursor.replace(/(^|\s)\/([^\s/]*)$/, "$1");
        const nextValue = `${updatedBeforeCursor}${textAfterCursor}`.replace(/\s{2,}/g, " ").trimStart();

        questionTextarea.value = nextValue;
        aplicarContextoAuditoria(commandValue);
        cerrarSlashMenu();
        actualizarContadorCaracteres(questionTextarea.value.length);
        actualizarEstadoEnvio();
        ajustarAlturaTextarea();
        questionTextarea.focus();
    }

    function aplicarContextoAuditoria(commandValue) {
        state.selectedAuditoria = commandValue || chatbotConfig.defaultAuditoria || "auto";
        if (hiddenAuditoria) {
            hiddenAuditoria.value = state.selectedAuditoria;
        }
        renderizarContextoActivo();
    }

    function renderizarContextoActivo() {
        if (!contextChip || !contextValue) {
            return;
        }

        const defaultAuditoria = chatbotConfig.defaultAuditoria || "auto";
        if (!state.selectedAuditoria || state.selectedAuditoria === defaultAuditoria) {
            contextChip.hidden = true;
            contextValue.textContent = "";
            return;
        }

        const activeCommand = slashCommands.find(function (command) {
            return command.value === state.selectedAuditoria;
        });

        contextValue.textContent = activeCommand?.label || state.selectedAuditoria;
        contextChip.hidden = false;
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function renderAssistantContent(content) {
        const rawContent = typeof content === "string" ? content.trim() : "";
        if (!rawContent) {
            return "";
        }

        if (rawContent.startsWith("<")) {
            return rawContent;
        }

        return escapeHtml(rawContent).replace(/\n/g, "<br>");
    }

    function buildTimestamp() {
        return new Date().toLocaleTimeString("es-MX", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function hideWelcomeMessage() {
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }

    function showUserMessage(messageText) {
        hideWelcomeMessage();

        const userMessage = document.createElement("div");
        userMessage.className = "chat-message user";
        userMessage.innerHTML = `
            <div class="message-header">
                <span class="message-avatar">TU</span>
                <span class="message-sender">Tú</span>
                <span class="message-time">${buildTimestamp()}</span>
            </div>
            <div class="message-content">${escapeHtml(messageText)}</div>
        `;

        chatBox.appendChild(userMessage);
        scrollToBottom();
    }

    function showBotMessage(messageContent, context) {
        hideWelcomeMessage();

        const botMessage = document.createElement("div");
        botMessage.className = "chat-message bot";
        botMessage.innerHTML = `
            <div class="message-header">
                <span class="message-avatar">CB</span>
                <span class="message-sender">${escapeHtml(botName)}</span>
                <span class="message-time">${buildTimestamp()}</span>
            </div>
            <div class="message-content">${renderAssistantContent(messageContent)}</div>
            ${context ? `<div class="message-context"><small>${escapeHtml(context)}</small></div>` : ""}
        `;

        chatBox.appendChild(botMessage);
        scrollToBottom();
        return botMessage;
    }

    function setProcessingState(processing) {
        state.isProcessing = processing;
        questionTextarea.disabled = processing;
        sendButton.disabled = processing || !questionTextarea.value.trim();

        if (processing) {
            sendButton.classList.add("loading");
            sendButton.innerHTML = '<span class="send-icon">...</span>';
        } else {
            sendButton.classList.remove("loading");
            sendButton.innerHTML = '<span class="send-icon">➤</span>';
        }
    }

    function validarContenido(texto) {
        const errores = [];
        const maxLength = chatbotConfig.maxQuestionLength || 2000;

        if (texto.length < 3) {
            errores.push("La consulta es muy corta.");
        }

        if (texto.length > maxLength) {
            errores.push(`La consulta supera el máximo de ${maxLength} caracteres.`);
        }

        return errores;
    }

    async function enviarPregunta() {
        const question = questionTextarea.value.trim();
        const errores = validarContenido(question);

        if (!question || errores.length > 0) {
            if (errores.length > 0) {
                showBotMessage(`
                    <div class="validation-error">
                        <p><strong>No pude enviar la consulta.</strong></p>
                        <p>${errores.join(" ")}</p>
                    </div>
                `);
            }
            return;
        }

        showUserMessage(question);
        setProcessingState(true);

        const loadingMessage = showBotMessage(`
            <div class="loading-message">
                <p><strong>Consultando la base normativa...</strong></p>
                <div class="loading-spinner"></div>
            </div>
        `);

        const formData = new FormData();
        formData.append("question", question);
        formData.append("auditoria", hiddenAuditoria?.value || chatbotConfig.defaultAuditoria || "auto");
        formData.append("ente", hiddenEnte?.value || chatbotConfig.defaultEnte || "No aplica");

        try {
            const response = await fetchConTimeout("/ask", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();

            loadingMessage.remove();

            if (data.success) {
                showBotMessage(data.answer, construirContextoRespuesta(data));
            } else {
                showBotMessage(`
                    <div class="error-message">
                        <p><strong>No pude procesar la consulta.</strong></p>
                        <p>${escapeHtml(data.message || "Ocurrió un error inesperado.")}</p>
                    </div>
                `);
            }
        } catch (error) {
            loadingMessage.remove();
            showBotMessage(`
                <div class="error-message">
                    <p><strong>Error de conexión.</strong></p>
                    <p>Intenta nuevamente en unos momentos.</p>
                </div>
            `);
            console.error("Error enviando consulta:", error);
        } finally {
            questionTextarea.value = "";
            actualizarContadorCaracteres(0);
            ajustarAlturaTextarea();
            cerrarSlashMenu();
            setProcessingState(false);
            questionTextarea.focus();
        }
    }

    function construirContextoRespuesta(data) {
        const partes = [];

        if (data.auditoria_label) {
            partes.push(data.auditoria_label);
        }

        if (Array.isArray(data.auditorias_consultadas) && data.auditorias_consultadas.length > 1) {
            partes.push(data.auditorias_consultadas.join(" / "));
        }

        if (typeof data.normativas_encontradas === "number") {
            const label = data.normativas_encontradas === 1 ? "1 coincidencia" : `${data.normativas_encontradas} coincidencias`;
            partes.push(label);
        }

        return partes.join(" • ");
    }

    async function fetchConTimeout(url, options) {
        const controller = new AbortController();
        const timeoutId = setTimeout(function () {
            controller.abort();
        }, 45000);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    function scrollToBottom(behavior = "smooth") {
        requestAnimationFrame(function () {
            chatBox.scrollTo({
                top: chatBox.scrollHeight,
                behavior,
            });
        });
    }
});
