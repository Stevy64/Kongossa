/**
 * Telegram-like Chat JavaScript
 * Gestion du chat en temps réel avec Polling (AJAX)
 */

class TelegramChat {
    constructor() {
        this.conversationId = null;
        this.currentUserId = window.currentUserId || null;
        this.pollingInterval = null;
        this.messagesArea = document.getElementById('chat-messages-area');
        this.messageInput = document.getElementById('chat-message-input');
        this.sendButton = document.getElementById('chat-send-button');
        this.isTyping = false;
        this.typingTimeout = null;
        this.lastMessageId = null;
        this.isLoadingMessages = false;
        this.hasMoreMessages = true;
        this.messageGroups = new Map(); // Pour grouper les messages par auteur
        this.pollingIntervalMs = 2000; // Polling toutes les 2 secondes
        
        this.init();
    }
    
    init() {
        if (!this.messagesArea) return;
        
        // Auto-scroll au chargement
        this.scrollToBottom();
        
        // Infinite scroll
        this.setupInfiniteScroll();
        
        // Auto-expanding textarea
        this.setupAutoExpandingTextarea();
        
        // Send message handler
        this.setupSendMessage();
        
        // Typing indicator
        this.setupTypingIndicator();
        
        // File upload
        this.setupFileUpload();
    }
    
    /**
     * Démarrer le polling pour récupérer les nouveaux messages
     */
    startPolling(conversationId) {
        // Arrêter le polling précédent si existant
        this.stopPolling();
        
        this.conversationId = conversationId;
        
        // Récupérer le dernier message ID pour initialiser le polling
        this.updateLastMessageId();
        
        // Démarrer le polling
        this.pollingInterval = setInterval(() => {
            this.pollNewMessages();
        }, this.pollingIntervalMs);
    }
    
    /**
     * Arrêter le polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    /**
     * Mettre à jour le dernier message ID
     */
    updateLastMessageId() {
        const messages = this.messagesArea?.querySelectorAll('[data-message-id]');
        if (messages && messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const messageId = lastMessage.getAttribute('data-message-id');
            if (messageId && !messageId.toString().startsWith('temp_')) {
                this.lastMessageId = parseInt(messageId);
            }
        }
    }
    
    /**
     * Polling pour récupérer les nouveaux messages
     */
    async pollNewMessages() {
        if (!this.conversationId || this.isLoadingMessages) return;
        
        try {
            const url = `/chat/${this.conversationId}/new-messages/`;
            const params = this.lastMessageId ? `?last_message_id=${this.lastMessageId}` : '';
            
            const response = await fetch(url + params, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    // Ajouter les nouveaux messages
                    data.messages.forEach(message => {
                        // Vérifier si le message n'existe pas déjà
                        if (!document.querySelector(`[data-message-id="${message.id}"]`)) {
                            this.addMessageToDOM(message, true);
                            this.markMessageAsRead(message.id);
                            this.lastMessageId = Math.max(this.lastMessageId || 0, message.id);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Erreur lors du polling:', error);
        }
    }
    
    /**
     * Ajouter un message au DOM
     */
    addMessageToDOM(messageData, shouldScroll = false) {
        // Chercher le conteneur de messages (peut être chat-messages-area ou chat-messages-container)
        if (!this.messagesArea) {
            this.messagesArea = document.getElementById('chat-messages-area') || document.getElementById('chat-messages-container');
        }
        if (!this.messagesArea) return;
        
        // Si c'est un vrai message (pas temporaire), chercher et remplacer le message temporaire correspondant
        if (!messageData.id.toString().startsWith('temp_')) {
            // Chercher un message temporaire qui pourrait correspondre (par contenu et expéditeur)
            const tempMessages = document.querySelectorAll('[data-temp-id]');
            tempMessages.forEach(tempMsg => {
                const tempContent = tempMsg.querySelector('.message-content')?.textContent?.trim();
                const messageContent = messageData.content?.trim();
                
                // Si le contenu correspond et que c'est le même expéditeur, remplacer
                if (tempContent === messageContent && 
                    tempMsg.closest('.message-group.sent') && 
                    messageData.sender_id === this.currentUserId) {
                    const tempGroup = tempMsg.closest('.message-group');
                    const bubblesContainer = tempGroup?.querySelector('.flex.flex-col');
                    if (bubblesContainer) {
                        tempMsg.remove();
                    }
                }
            });
            
            // Vérifier si le message existe déjà
            if (document.querySelector(`[data-message-id="${messageData.id}"]`)) {
                return;
            }
        }
        
        const isSent = messageData.sender_id === this.currentUserId;
        const messageGroup = this.getMessageGroup(messageData, isSent);
        
        // Créer la bulle de message
        const messageBubble = this.createMessageBubble(messageData, isSent);
        
        // Trouver le conteneur de bulles dans le groupe
        let bubblesContainer = messageGroup.querySelector('.flex.flex-col');
        if (!bubblesContainer) {
            bubblesContainer = document.createElement('div');
            bubblesContainer.className = 'flex flex-col gap-0.5';
            messageGroup.appendChild(bubblesContainer);
        } else {
            // Si le groupe existe déjà, utiliser le conteneur existant
            bubblesContainer = messageGroup.querySelector('.flex.flex-col');
        }
        
        bubblesContainer.appendChild(messageBubble);
        
        // Ajouter le groupe au DOM s'il n'existe pas
        if (!messageGroup.parentElement) {
            // Chercher le conteneur approprié (chat-messages-container ou chat-messages-area)
            const container = document.getElementById('chat-messages-container') || this.messagesArea;
            container.appendChild(messageGroup);
        }
        
        if (shouldScroll) {
            this.scrollToBottom(true);
        }
    }
    
    /**
     * Obtenir ou créer un groupe de messages
     */
    getMessageGroup(messageData, isSent) {
        const groupKey = `${messageData.sender_id}_${this.getDateKey(messageData.created_at)}`;
        
        if (!this.messageGroups.has(groupKey)) {
            const group = document.createElement('div');
            group.className = `message-group ${isSent ? 'sent' : 'received'}`;
            group.dataset.groupKey = groupKey;
            
            // Ajouter l'avatar pour les messages reçus
            if (!isSent) {
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                if (messageData.sender_avatar) {
                    const img = document.createElement('img');
                    img.src = messageData.sender_avatar;
                    img.alt = messageData.sender;
                    avatar.appendChild(img);
                } else {
                    const span = document.createElement('span');
                    span.textContent = (messageData.sender || '?')[0].toUpperCase();
                    avatar.appendChild(span);
                }
                group.appendChild(avatar);
            }
            
            // Créer le conteneur pour les bulles
            const bubblesContainer = document.createElement('div');
            bubblesContainer.className = 'flex flex-col gap-0.5';
            group.appendChild(bubblesContainer);
            
            this.messageGroups.set(groupKey, group);
        }
        
        return this.messageGroups.get(groupKey);
    }
    
    /**
     * Créer une bulle de message
     */
    createMessageBubble(messageData, isSent) {
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${isSent ? 'sent message-out' : 'received message-in'}`;
        bubble.dataset.messageId = messageData.id;
        
        let content = '';
        
        // Contenu texte
        if (messageData.content) {
            content += `<div class="message-content">${this.formatMessageContent(messageData.content)}</div>`;
        }
        
        // Média (image, vidéo, audio)
        if (messageData.image) {
            content += `<div class="message-media"><img src="${messageData.image}" alt="Image" loading="lazy"></div>`;
        } else if (messageData.video) {
            content += `<div class="message-media"><video src="${messageData.video}" controls></video></div>`;
        } else if (messageData.audio) {
            content += `<div class="message-media"><audio src="${messageData.audio}" controls></audio></div>`;
        } else if (messageData.file) {
            content += this.createFileMessage(messageData);
        }
        
        // Footer avec timestamp et read receipt
        const time = this.formatTime(messageData.created_at);
        const readReceipt = isSent ? this.createReadReceipt(messageData.read_at) : '';
        
        content += `
            <div class="message-footer">
                <span class="message-time">${time}</span>
                ${readReceipt}
            </div>
        `;
        
        bubble.innerHTML = content;
        return bubble;
    }
    
    /**
     * Créer un message de fichier
     */
    createFileMessage(messageData) {
        const fileName = messageData.file_name || 'Fichier';
        const fileSize = this.formatFileSize(messageData.file_size || 0);
        
        return `
            <div class="message-file">
                <div class="message-file-icon">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                </div>
                <div class="message-file-info">
                    <div class="message-file-name">${fileName}</div>
                    <div class="message-file-size">${fileSize}</div>
                </div>
                <a href="${messageData.file}" download class="text-telegram-blue hover:underline">Télécharger</a>
            </div>
        `;
    }
    
    /**
     * Créer le read receipt (double check)
     */
    createReadReceipt(readAt) {
        if (!readAt) {
            return '<div class="read-receipt single"><svg fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg></div>';
        }
        
        return '<div class="read-receipt double"><svg fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg><svg fill="currentColor" viewBox="0 0 20 20" style="margin-left: -8px;"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg></div>';
    }
    
    /**
     * Formater le contenu du message (liens, etc.)
     */
    formatMessageContent(content) {
        // Échapper HTML
        content = content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        
        // Détecter les liens
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank" class="text-telegram-blue-light underline">$1</a>');
        
        // Détecter les retours à la ligne
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    /**
     * Formater l'heure
     */
    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Moins d'une minute
            return 'maintenant';
        } else if (diff < 3600000) { // Moins d'une heure
            const minutes = Math.floor(diff / 60000);
            return `il y a ${minutes} min`;
        } else if (date.toDateString() === now.toDateString()) { // Aujourd'hui
            return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        } else {
            return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
        }
    }
    
    /**
     * Formater la taille de fichier
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    /**
     * Obtenir la clé de date pour grouper les messages
     */
    getDateKey(isoString) {
        const date = new Date(isoString);
        return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
    }
    
           /**
            * Scroll vers le bas
            */
           scrollToBottom(smooth = false) {
               if (!this.messagesArea) {
                   this.messagesArea = document.getElementById('chat-messages-area') || document.getElementById('chat-messages-container');
               }
               if (!this.messagesArea) return;
               
               // Utiliser requestAnimationFrame pour un scroll plus fluide
               requestAnimationFrame(() => {
                   this.messagesArea.scrollTo({
                       top: this.messagesArea.scrollHeight,
                       behavior: smooth ? 'smooth' : 'auto'
                   });
               });
           }
    
    /**
     * Infinite scroll
     */
    setupInfiniteScroll() {
        if (!this.messagesArea) return;
        
        this.messagesArea.addEventListener('scroll', () => {
            if (this.messagesArea.scrollTop === 0 && this.hasMoreMessages && !this.isLoadingMessages) {
                this.loadMoreMessages();
            }
        });
    }
    
    /**
     * Charger plus de messages
     */
    async loadMoreMessages() {
        if (!this.conversationId || this.isLoadingMessages) return;
        
        this.isLoadingMessages = true;
        
        try {
            const response = await fetch(`/chat/${this.conversationId}/messages/?before=${this.lastMessageId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                const scrollHeight = this.messagesArea.scrollHeight;
                
                // Ajouter les messages en haut
                data.messages.reverse().forEach(msg => {
                    const isSent = msg.sender_id === this.currentUserId;
                    const messageGroup = this.getMessageGroup(msg, isSent);
                    const bubble = this.createMessageBubble(msg, isSent);
                    messageGroup.insertBefore(bubble, messageGroup.firstChild);
                    
                    if (!messageGroup.parentElement) {
                        this.messagesArea.insertBefore(messageGroup, this.messagesArea.firstChild);
                    }
                });
                
                // Maintenir la position de scroll
                const newScrollHeight = this.messagesArea.scrollHeight;
                this.messagesArea.scrollTop = newScrollHeight - scrollHeight;
                
                this.lastMessageId = data.messages[0].id;
            } else {
                this.hasMoreMessages = false;
            }
        } catch (error) {
            console.error('Erreur lors du chargement des messages:', error);
        } finally {
            this.isLoadingMessages = false;
        }
    }
    
    /**
     * Auto-expanding textarea
     */
    setupAutoExpandingTextarea() {
        if (!this.messageInput) return;
        
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 128) + 'px';
        });
    }
    
    /**
     * Envoyer un message
     */
    setupSendMessage() {
        if (!this.sendButton || !this.messageInput) return;
        
        const sendMessage = () => {
            const content = this.messageInput.value.trim();
            if (!content && !this.hasMediaToSend()) return;
            
            this.sendMessage(content);
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
        };
        
        this.sendButton.addEventListener('click', sendMessage);
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    /**
     * Vérifier s'il y a des médias à envoyer
     */
    hasMediaToSend() {
        const fileInput = document.getElementById('chat-file-input');
        return fileInput && fileInput.files.length > 0;
    }
    
    /**
     * Envoyer un message via WebSocket ou HTTP
     */
    async sendMessage(content) {
        if (!this.conversationId) return;
        
        const formData = new FormData();
        formData.append('content', content);
        
        const fileInput = document.getElementById('chat-file-input');
        if (fileInput && fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }
        
        try {
            const response = await fetch(`/chat/${this.conversationId}/send/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                // Le message sera ajouté via WebSocket
                if (fileInput) fileInput.value = '';
            }
        } catch (error) {
            console.error('Erreur lors de l\'envoi:', error);
        }
    }
    
    /**
     * Typing indicator (désactivé avec polling, peut être réimplémenté avec une API séparée si nécessaire)
     */
    setupTypingIndicator() {
        // Le typing indicator nécessiterait une API séparée avec polling
        // Pour l'instant, on le désactive
        if (!this.messageInput) return;
        
        // Optionnel: Implémenter le typing indicator avec une API séparée
        // this.messageInput.addEventListener('input', () => {
        //     // Envoyer un signal de typing via API
        // });
    }
    
    /**
     * Afficher l'indicateur de frappe
     */
    showTypingIndicator(username) {
        let indicator = document.getElementById('typing-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'typing-indicator';
            indicator.className = 'typing-indicator';
            indicator.innerHTML = `
                <span>${username} est en train d'écrire</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            `;
            this.messagesArea.appendChild(indicator);
        }
        this.scrollToBottom(true);
    }
    
    /**
     * Masquer l'indicateur de frappe
     */
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    /**
     * File upload
     */
    setupFileUpload() {
        const fileInput = document.getElementById('chat-file-input');
        const attachButton = document.getElementById('chat-attach-button');
        
        if (attachButton && fileInput) {
            attachButton.addEventListener('click', () => fileInput.click());
        }
    }
    
    /**
     * Marquer un message comme lu
     */
    async markMessageAsRead(messageId) {
        try {
            await fetch(`/chat/messages/${messageId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Erreur lors du marquage comme lu:', error);
        }
    }
    
    /**
     * Mettre à jour le read receipt
     */
    updateReadReceipt(messageId) {
        const message = document.querySelector(`[data-message-id="${messageId}"]`);
        if (message) {
            const receipt = message.querySelector('.read-receipt');
            if (receipt) {
                receipt.className = 'read-receipt double';
                receipt.innerHTML = '<svg fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg><svg fill="currentColor" viewBox="0 0 20 20" style="margin-left: -8px;"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg>';
            }
        }
    }
    
    /**
     * Obtenir le token CSRF
     */
    getCSRFToken() {
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        return cookie ? cookie[1] : '';
    }
    
    /**
     * Méthode de compatibilité pour l'ancien code qui appelait connectWebSocket
     */
    connectWebSocket(conversationId) {
        // Rediriger vers startPolling pour la compatibilité
        this.startPolling(conversationId);
    }
}

// Initialiser le chat quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    window.telegramChat = new TelegramChat();
});

