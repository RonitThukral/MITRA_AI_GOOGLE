// ======================= MAIN CHAT FUNCTIONALITY =======================
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const toastEl = document.getElementById('toast');
const savedChatsEl = document.getElementById('saved-chats');
const newChatBtn = document.getElementById('new-chat');
const clearBtn = document.getElementById('clear-btn');
const themeToggle = document.getElementById('theme-toggle');
const openSidebar = document.getElementById('open-sidebar');
const sidebar = document.getElementById('sidebar');
const audioPlayer = document.getElementById('audio-player');
const micBtn = document.getElementById('mic-btn');
const careerToggle = document.getElementById('career-toggle');
const careerBadge = document.getElementById('career-badge');
const modeStatus = document.getElementById('mode-status');
const modeIndicator = document.getElementById('mode-indicator');
const searchStatus = document.getElementById('search-status');

let isDark = true;
let isSending = false;
let sessionChats = [];
let currentMode = "text";
let careerSuggestActive = false;

inputEl.focus();

function showToast(message, kind = 'info') {
    const bgColor = kind === 'error' ? 'bg-red-500' : kind === 'success' ? 'bg-green-500' : 'bg-blue-500';
    toastEl.innerHTML = `<div class="px-4 py-2 rounded-lg shadow-lg ${bgColor} text-white text-sm">${message}</div>`;
    toastEl.classList.remove('hidden');
    setTimeout(() => { toastEl.classList.add('hidden'); }, 3000);
}

function updateModeUI() {
    if (careerSuggestActive) {
        careerBadge.classList.remove('hidden');
        searchStatus.classList.remove('hidden');
        searchStatus.textContent = 'Career Mode Active';
        modeStatus.textContent = 'Career Guidance + Mental Health';
        modeStatus.className = 'text-green-400';
        modeIndicator.innerHTML = '<span class="text-green-400">Career Guidance Active</span>';
    } else {
        careerBadge.classList.add('hidden');
        searchStatus.classList.add('hidden');
        modeStatus.textContent = 'Mental Health Mode';
        modeStatus.className = 'text-purple-400';
        modeIndicator.innerHTML = '<span class="text-gray-400">Mental Health Support</span>';
    }
}

// Career toggle functionality
careerToggle.addEventListener('click', () => {
    careerSuggestActive = !careerSuggestActive;
    careerToggle.classList.toggle('active', careerSuggestActive);
    updateModeUI();
    
    const message = careerSuggestActive ? 
        'Career Suggest mode activated! Ask me about educational paths, career options, or academic planning with real-time web search.' :
        'Career Suggest mode deactivated. Continuing with mental health support.';
    showToast(message, careerSuggestActive ? 'success' : 'info');
});

function addMessage({ role = 'assistant', text = '', id = null, ts = new Date() }, withTyping = false) {
    const container = document.createElement('div');
    container.className = 'max-w-3xl mx-auto px-4 py-4';
    
    const inner = document.createElement('div');
    inner.className = 'flex items-start gap-4';
    
    const avatar = document.createElement('div');
    avatar.className = 'w-10 h-10 rounded-full flex items-center justify-center font-bold text-white flex-shrink-0';
    
    if (role === 'user') {
        avatar.style.background = 'linear-gradient(45deg, #06b6d4, #0891b2)';
        avatar.textContent = 'U';
    } else {
        avatar.style.background = 'linear-gradient(45deg, #8b5cf6, #ec4899)';
        avatar.textContent = 'M';
    }

    const messageContainer = document.createElement('div');
    messageContainer.className = 'flex-1';
    
    const bubble = document.createElement('div');
    bubble.className = role === 'user' ? 
        'message-bubble p-5 rounded-2xl bg-blue-600 text-white max-w-[85%] ml-auto break-words' :
        'message-bubble p-5 rounded-2xl bg-gray-800 text-gray-100 max-w-[90%] break-words border border-gray-700';
    
    // CRITICAL: Add ai-response class for HTML formatting
    if (role === 'assistant') {
        bubble.classList.add('ai-response');
    }
    
    bubble.setAttribute('data-role', role);
    bubble.setAttribute('data-id', id || `m-${Date.now()}`);

    const timeEl = document.createElement('div');
    timeEl.className = 'text-xs text-gray-400 mt-2 px-1';

    if (withTyping) {
        bubble.innerHTML = `<span class="typing-indicator text-gray-400">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </span> MITRA is thinking...`;
    } else {
        // CRITICAL: Use innerHTML for AI responses to render HTML, textContent for user messages
        if (role === 'assistant') {
            bubble.innerHTML = text; // Render HTML for AI responses
        } else {
            bubble.textContent = text; // Plain text for user messages
        }
        timeEl.textContent = formatTime(ts);
    }

    if (role === 'user') {
        inner.appendChild(messageContainer);
        messageContainer.appendChild(bubble);
        inner.appendChild(avatar);
    } else {
        inner.appendChild(avatar);
        messageContainer.appendChild(bubble);
        inner.appendChild(messageContainer);
    }
    
    container.appendChild(inner);
    if (!withTyping) container.appendChild(timeEl);

    messagesEl.appendChild(container);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
}

function formatTime(d) {
    const dt = new Date(d);
    return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function resetComposer() { 
    inputEl.value = ''; 
    inputEl.style.height = 'auto'; 
    document.getElementById('charcount').textContent = '0'; 
}

function shouldShowSearch(text) {
    if (!careerSuggestActive) return false;
    
    const searchKeywords = [
        'cutoff', 'admission', '2024', '2025', 'latest', 'current',
        'ranking', 'fees', 'placement', 'eligibility', 'dates',
        'jee', 'neet', 'clat', 'gate', 'cat', 'requirements',
        'exam', 'application', 'form', 'notification'
    ];
    
    return searchKeywords.some(keyword => 
        text.toLowerCase().includes(keyword.toLowerCase())
    );
}

async function sendMessage(evt) {
    if (evt) evt.preventDefault();
    if (isSending) return;
    const text = inputEl.value.trim();
    if (!text) {
        showToast('Type a message to send', 'error');
        return;
    }

    addMessage({ role: 'user', text });
    sessionChats.push({ role: 'user', text, ts: new Date().toISOString() });
    resetComposer();

    let typingBubble = null;
    
    // Show search indicator for career queries
    if (careerSuggestActive && shouldShowSearch(text)) {
        searchStatus.textContent = 'Searching...';
        searchStatus.style.background = 'linear-gradient(45deg, #f59e0b, #d97706)';
    }
    
    if (currentMode === "text") {
        typingBubble = addMessage({ role: 'assistant', text: '', withTyping: true });
    }

    isSending = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ 
                message: text, 
                session_id: 'default', 
                system_key: 'mental_health_wellness',
                career_suggest: careerSuggestActive 
            })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Server error');

        currentMode = data.mode || 'text';

        // Update search status
        if (data.search_performed) {
            searchStatus.textContent = `Search: ${data.search_source || 'Complete'}`;
            searchStatus.style.background = 'linear-gradient(45deg, #059669, #10b981)';
        } else if (careerSuggestActive) {
            searchStatus.textContent = 'Career Mode Active';
            searchStatus.style.background = 'linear-gradient(45deg, #10b981, #059669)';
        }

        if (currentMode === "voice_assistant") {
            if (typingBubble) {
                messagesEl.removeChild(typingBubble.parentElement.parentElement.parentElement);
            }

            const audioUrl = `data:audio/mp3;base64,${data.audio}`;
            audioPlayer.src = audioUrl;
            audioPlayer.play();

            // Add the message bubble
            const bubble = addMessage({ role: 'assistant', text: data.text_reply });
            micBtn.classList.add('animate-pulse');

            // Append Go Live UI if crisis detected
            if (data.crisis_detected) {
                const goLiveDiv = document.createElement('div');
                goLiveDiv.className = 'mt-4 text-center border-t border-gray-700 pt-4';
                goLiveDiv.innerHTML = `
                    <p class="text-gray-300 mb-3 text-sm">Need more immediate support? Let's talk live.</p>
                    <button class="go-live-btn inline-flex items-center gap-2 bg-accent-purple hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors font-medium shadow-lg">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                        Go Live with MITRA
                    </button>
                `;
                bubble.appendChild(goLiveDiv);
            }
        } else {
            let reply = data.reply || 'No reply';
            
            micBtn.classList.remove('animate-pulse');

            if (typingBubble) {
                await simulateTyping(typingBubble, reply);
            } else {
                // CRITICAL: HTML will be rendered due to ai-response class
                addMessage({ role: 'assistant', text: reply });
            }

            sessionChats.push({ role: 'assistant', text: reply, ts: new Date().toISOString() });
        }

        // Show success toast for search
        if (data.search_performed) {
            showToast(`Web search completed via ${data.search_source || 'search API'}`, 'success');
        }

    } catch (err) {
        console.error(err);
        
        // Reset search status on error
        if (careerSuggestActive) {
            searchStatus.textContent = 'Search Error';
            searchStatus.style.background = 'linear-gradient(45deg, #dc2626, #b91c1c)';
        }
        
        if (typingBubble) {
            typingBubble.innerHTML = '⚠️ Error: ' + (err.message || 'Failed to fetch');
        } else {
            addMessage({ role: 'assistant', text: '⚠️ Error: ' + (err.message || 'Failed to fetch') });
        }
        showToast('Error: ' + (err.message || 'Please try again'), 'error');
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
}

function simulateTyping(bubbleEl, text) {
    return new Promise((resolve) => {
        let i = 0;
        bubbleEl.innerHTML = '';
        const contentWrp = document.createElement('div');
        bubbleEl.appendChild(contentWrp);
        const baseSpeed = 12;
        
        function step() {
            if (i >= text.length) {
                const timeEl = document.createElement('div');
                timeEl.className = 'text-xs text-gray-400 mt-2';
                timeEl.textContent = formatTime(new Date());
                bubbleEl.parentElement.parentElement.appendChild(timeEl);
                resolve();
                return;
            }
            
            // CRITICAL: For AI responses, use innerHTML to render HTML
            if (bubbleEl.classList.contains('ai-response')) {
                contentWrp.innerHTML = text.slice(0, i + 1);
            } else {
                contentWrp.textContent = text.slice(0, i + 1);
            }
            
            i++;
            let delay = baseSpeed + (Math.random() * 20);
            const char = text[i] || '';
            if (char === ',' || char === ';') delay += 80;
            if (char === '.' || char === '!' || char === '?') delay += 120;
            if (char === '\n') delay += 150;
            setTimeout(step, delay);
        }
        step();
    });
}

// ======================= LIVE SESSION FUNCTIONALITY =======================
const liveSessionOverlay = document.getElementById('live-session-overlay');
const closeLiveSession = document.getElementById('close-live-session');
const startVoiceBtn = document.getElementById('start-voice');
const stopVoiceBtn = document.getElementById('stop-voice');
const videoElement = document.getElementById('videoElement');
const canvasElement = document.getElementById('canvasElement');
const liveChatLog = document.getElementById('live-chat-log');
const liveStatus = document.getElementById('live-status');

let liveWebSocket = null;
let stream = null;
let currentFrameB64 = null;
let audioContext = null;
let processor = null;
let pcmData = [];
let recordInterval = null;
let audioInputContext = null;
let workletNode = null;
let initialized = false;

// Open live session when mic button is clicked
micBtn.addEventListener('click', async () => {
    if (currentMode === "voice_assistant") {
        // If already in voice mode, just show a message
        showToast('You are already in voice assistance mode. MITRA is speaking to you.');
        return;
    }
    
    liveSessionOverlay.classList.remove('hidden');
    await startWebcam();
    connectToLiveSession();
});

// Close live session
closeLiveSession.addEventListener('click', () => {
    if (liveWebSocket) {
        liveWebSocket.close();
    }
    stopAudioInput();
    stopWebcam();
    liveSessionOverlay.classList.add('hidden');
    liveStatus.textContent = 'Ready to connect';
    
    // Send automatic check-in message when returning from live session
    sendAutomaticCheckIn();
});






async function sendAutomaticCheckIn() {
    // Add a slight delay for better UX
    setTimeout(async () => {
        const checkInMessage = "I just returned from the live session";
        
        // Add typing indicator
        const typingBubble = addMessage({ role: 'assistant', text: '', withTyping: true });
        
        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ 
                    message: checkInMessage,
                    session_id: 'default', 
                    system_key: 'mental_health_wellness',
                    career_suggest: careerSuggestActive,
                    post_live_session: 'true' // Special flag
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server error');

            // Remove typing indicator
            if (typingBubble) {
                messagesEl.removeChild(typingBubble.parentElement.parentElement.parentElement);
            }

            // Handle voice response
            if (data.mode === "voice_assistant" && data.audio) {
                const audioUrl = `data:audio/mp3;base64,${data.audio}`;
                audioPlayer.src = audioUrl;
                audioPlayer.play();
                
                // Add the message bubble
                addMessage({ role: 'assistant', text: data.text_reply || data.reply });
                micBtn.classList.add('animate-pulse');
            }

        } catch (err) {
            console.error(err);
            if (typingBubble) {
                typingBubble.innerHTML = '⚠️ Error checking in';
            }
        }
    }, 1500); // 1.5 second delay
}







// Start webcam
async function startWebcam() {
    try {
        const constraints = {
            video: {
                width: { max: 640 },
                height: { max: 480 },
            },
        };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElement.srcObject = stream;
        
        // Start capturing frames
        setInterval(captureImage, 3000);
    } catch (err) {
        console.error("Error accessing webcam: ", err);
        showToast('Camera access denied. Voice-only mode will be used.');
    }
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

function captureImage() {
    if (stream && videoElement.videoWidth > 0) {
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        const context = canvasElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
        const imageData = canvasElement.toDataURL("image/jpeg").split(",")[1].trim();
        currentFrameB64 = imageData;
    }
}

// Connect to live session WebSocket
function connectToLiveSession() {
    const wsUrl = `ws://${window.location.host}/live-session`;
    liveWebSocket = new WebSocket(wsUrl);

    liveWebSocket.onopen = () => {
        liveStatus.textContent = 'Connected';
        sendInitialSetupMessage();
    };

    liveWebSocket.onclose = () => {
        liveStatus.textContent = 'Disconnected';
        showToast('Live session ended');
    };

    liveWebSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        liveStatus.textContent = 'Connection error';
        showToast('Connection failed');
    };

    liveWebSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.text) {
            addToLiveChatLog('MITRA: ' + data.text);
        }
        if (data.audio) {
            playLiveAudio(data.audio);
        }
    };
}

function sendInitialSetupMessage() {
    const systemInstruction = "You are a compassionate mental health support assistant named MITRA for live voice conversations. Provide warm, empathetic responses and be a good listener. Keep responses concise and natural for voice interaction.";
    
    const setupMessage = {
        setup: {
            system_instruction: {
                parts: [{ text: systemInstruction }]
            },
            generation_config: { response_modalities: ["AUDIO"] },
        },
    };

    liveWebSocket.send(JSON.stringify(setupMessage));
}

function addToLiveChatLog(message) {
    const p = document.createElement('p');
    p.textContent = message;
    p.className = 'mb-2';
    liveChatLog.appendChild(p);
    liveChatLog.scrollTop = liveChatLog.scrollHeight;
}

// Audio processing for live session
async function initializeAudioContext() {
    if (initialized) return;

    audioInputContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    await audioInputContext.audioWorklet.addModule("/static/pcm-processor.js");
    workletNode = new AudioWorkletNode(audioInputContext, "pcm-processor");
    workletNode.connect(audioInputContext.destination);
    initialized = true;
}

function base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

function convertPCM16LEToFloat32(pcmData) {
    const inputArray = new Int16Array(pcmData);
    const float32Array = new Float32Array(inputArray.length);

    for (let i = 0; i < inputArray.length; i++) {
        float32Array[i] = inputArray[i] / 32768;
    }
    return float32Array;
}

async function playLiveAudio(base64AudioChunk) {
    try {
        if (!initialized) {
            await initializeAudioContext();
        }

        if (audioInputContext.state === "suspended") {
            await audioInputContext.resume();
        }
        
        const arrayBuffer = base64ToArrayBuffer(base64AudioChunk);
        const float32Data = convertPCM16LEToFloat32(arrayBuffer);
        workletNode.port.postMessage(float32Data);
    } catch (error) {
        console.error("Error processing audio chunk:", error);
    }
}

function recordChunk() {
    const buffer = new ArrayBuffer(pcmData.length * 2);
    const view = new DataView(buffer);
    pcmData.forEach((value, index) => {
        view.setInt16(index * 2, value, true);
    });

    const base64 = btoa(String.fromCharCode.apply(null, new Uint8Array(buffer)));
    sendVoiceMessage(base64);
    pcmData = [];
}

function sendVoiceMessage(b64PCM) {
    if (!liveWebSocket || liveWebSocket.readyState !== WebSocket.OPEN) {
        console.log("WebSocket not ready");
        return;
    }

    const payload = {
        realtime_input: {
            media_chunks: [
                {
                    mime_type: "audio/pcm",
                    data: b64PCM,
                }
            ],
        },
    };

    // Add image if available
    if (currentFrameB64) {
        payload.realtime_input.media_chunks.push({
            mime_type: "image/jpeg",
            data: currentFrameB64,
        });
    }

    liveWebSocket.send(JSON.stringify(payload));
}

async function startAudioInput() {
    try {
        audioContext = new AudioContext({ sampleRate: 16000 });

        const audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
            },
        });

        const source = audioContext.createMediaStreamSource(audioStream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcm16[i] = inputData[i] * 0x7fff;
            }
            pcmData.push(...pcm16);
        };

        source.connect(processor);
        processor.connect(audioContext.destination);

        recordInterval = setInterval(recordChunk, 3000);
        liveStatus.textContent = 'Recording...';
        startVoiceBtn.classList.add('active');
    } catch (err) {
        console.error("Error starting audio input:", err);
        showToast('Microphone access denied');
    }
}

function stopAudioInput() {
    if (processor) {
        processor.disconnect();
    }
    if (audioContext) {
        audioContext.close();
    }
    if (recordInterval) {
        clearInterval(recordInterval);
    }
    
    liveStatus.textContent = 'Connected';
    startVoiceBtn.classList.remove('active');
}

// Live session event listeners
startVoiceBtn.addEventListener('click', startAudioInput);
stopVoiceBtn.addEventListener('click', stopAudioInput);

// ======================= REGULAR CHAT EVENT LISTENERS =======================
inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = (inputEl.scrollHeight) + 'px';
    document.getElementById('charcount').textContent = inputEl.value.length;
});

inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

document.getElementById('composer').addEventListener('submit', sendMessage);

newChatBtn.addEventListener('click', () => {
    messagesEl.innerHTML = '';
    sessionChats = [];
    currentMode = "text";
    micBtn.classList.remove('animate-pulse');
    micBtn.style.background = '';
    
    const welcomeHtml = `
    <div class="search-response">
        <p><span class="search-icon">🧠</span> <strong>Hello! I'm MITRA, your AI companion for mental health support and career guidance.</strong></p>
        
        <h3>🎯 How I Can Help You</h3>
        <ul>
            <li><strong>Mental Health:</strong> Emotional support, coping strategies, and wellness tips</li>
            <li><strong>Career Guidance:</strong> Educational pathways, career options, and real-time information</li>
            <li><strong>Live Voice Chat:</strong> Real-time conversations with voice and video</li>
        </ul>
        
        <h3>💡 Getting Started</h3>
        <p>Toggle the <strong>"Career Suggest"</strong> feature in the sidebar for specialized career counseling with live web search capabilities.</p>
        
        <h3>🔗 Ready to Help</h3>
        <p>What would you like to talk about today?</p>
    </div>`;
    
    addMessage({ role: 'assistant', text: welcomeHtml });
});

clearBtn.addEventListener('click', () => {
    messagesEl.innerHTML = '';
    sessionChats = [];
    currentMode = "text";
    micBtn.classList.remove('animate-pulse');
    micBtn.style.background = '';
    addMessage({ role: 'assistant', text: "Conversation cleared. I'm still here to support you whenever you need." });
});

themeToggle.addEventListener('click', () => {
    isDark = !isDark;
    if (isDark) {
        document.documentElement.classList.add('dark');
        themeToggle.innerHTML = `
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
            Dark mode
        `;
        showToast('Dark mode enabled');
    } else {
        document.documentElement.classList.remove('dark');
        themeToggle.innerHTML = `
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707"/>
            </svg>
            Light mode
        `;
        showToast('Light mode enabled');
    }
});

openSidebar.addEventListener('click', () => {
    if (sidebar.style.display === 'flex') {
        sidebar.style.display = 'none';
    } else {
        sidebar.style.display = 'flex';
    }
});

function loadSavedChats() {
    savedChatsEl.innerHTML = '';
    const demoChats = [
        { title: 'JEE Main 2025 dates', id: 'd1' },
        { title: 'Career after 12th PCM', id: 'd2' },
        { title: 'NEET counseling process', id: 'd3' },
        { title: 'Engineering vs Medical', id: 'd4' },
        { title: 'Managing study stress', id: 'd5' },
        { title: 'Anxiety support session', id: 'd6' }, 
        { title: 'Sleep concerns help', id: 'd7' }
    ];
    
    for (const chat of demoChats) {
        const li = document.createElement('li');
        li.className = 'px-3 py-2 rounded-lg hover:bg-gray-700 cursor-pointer text-sm text-gray-300 hover:text-white transition-colors';
        li.textContent = chat.title;
        li.addEventListener('click', () => {
            messagesEl.innerHTML = '';
            const loadingHtml = `
            <div class="search-response">
                <p><span class="search-icon">📂</span> <strong>Loading previous conversation: "${chat.title}"</strong></p>
                <p>This is a demo. Your conversation history will appear here in the full version.</p>
            </div>`;
            addMessage({ role: 'assistant', text: loadingHtml });
        });
        savedChatsEl.appendChild(li);
    }
}

// Initialize
loadSavedChats();
updateModeUI();

// Audio player events
audioPlayer.addEventListener('ended', () => {
    micBtn.classList.remove('animate-pulse');
    showToast('Voice response completed', 'info');
});

audioPlayer.addEventListener('play', () => {
    showToast('Playing voice response...', 'info');
});

// Scroll to bottom when new messages arrive
const observer = new MutationObserver(() => {
    messagesEl.scrollTop = messagesEl.scrollHeight;
});

observer.observe(messagesEl, {
    childList: true,
    subtree: true
});

// Make sendMessage globally accessible
window.sendMessage = sendMessage;

// Event delegation for Go Live button clicks in messages
messagesEl.addEventListener('click', async (e) => {
    if (e.target.classList.contains('go-live-btn')) {
        e.preventDefault(); // Prevent any default behavior
        
        // Reset current mode to allow live session transition
        currentMode = "text";
        micBtn.classList.remove('animate-pulse');
        
        // Show toast indicating transition to live session
        showToast('Switching to live video session...', 'info');
        
        liveSessionOverlay.classList.remove('hidden');
        await startWebcam();
        connectToLiveSession();
    }
});











































