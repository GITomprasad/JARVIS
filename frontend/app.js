/**
 * J.A.R.V.I.S. Neural Web Interface Controller
 * Handles real-time API communication, voice recognition, session state, and audio synthesis.
 */

// Global State
const state = {
  backendUrl: localStorage.getItem('jarvis_backend_url') || (window.location.origin.includes('http') ? window.location.origin : 'http://127.0.0.1:8000'),
  currentSession: localStorage.getItem('jarvis_session_id') || 'default',
  deviceId: 'web_neural_client',
  audioEnabled: localStorage.getItem('jarvis_audio_enabled') !== 'false',
  isProcessing: false,
  isRecording: false,
  activeTab: 'chat',
  speechRecognition: null,
  audioCtx: null
};

// Ensure backendUrl does not have a trailing slash
state.backendUrl = state.backendUrl.replace(/\/+$/, '');

// Web Audio API Sound Synthesizer (Zero External Audio Files)
function playTone(type) {
  if (!state.audioEnabled) return;
  try {
    if (!state.audioCtx) {
      state.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    const ctx = state.audioCtx;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;

    if (type === 'send') {
      // High-tech crisp chirp
      osc.type = 'sine';
      osc.frequency.setValueAtTime(580, now);
      osc.frequency.exponentialRampToValueAtTime(1050, now + 0.08);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === 'receive') {
      // Futuristic dual-harmonic chime
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.setValueAtTime(1320, now + 0.06);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (type === 'click') {
      // Subtle click
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, now);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.03);
      osc.start(now);
      osc.stop(now + 0.03);
    } else if (type === 'clear') {
      // Sweep down
      osc.type = 'sine';
      osc.frequency.setValueAtTime(700, now);
      osc.frequency.exponentialRampToValueAtTime(200, now + 0.15);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      osc.start(now);
      osc.stop(now + 0.15);
    }
  } catch (e) {
    console.debug('Audio error:', e);
  }
}

function toggleAudio() {
  state.audioEnabled = !state.audioEnabled;
  localStorage.setItem('jarvis_audio_enabled', state.audioEnabled);
  const icon = document.getElementById('audioIcon');
  if (icon) {
    icon.textContent = state.audioEnabled ? 'volume_up' : 'volume_off';
    icon.classList.toggle('text-primary', state.audioEnabled);
    icon.classList.toggle('text-outline', !state.audioEnabled);
  }
  playTone('click');
}

// -------------------------------------------------------------
// TAB SWITCHING
// -------------------------------------------------------------
function switchTab(tabName) {
  playTone('click');
  state.activeTab = tabName;

  const tabs = ['chat', 'actions', 'memory', 'system'];
  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    if (view) {
      view.classList.toggle('hidden', t !== tabName);
    }
    if (navBtn) {
      if (t === tabName) {
        navBtn.classList.remove('text-on-surface-variant');
        navBtn.classList.add('text-primary-container');
        navBtn.querySelector('span:last-child')?.classList.add('font-semibold');
      } else {
        navBtn.classList.add('text-on-surface-variant');
        navBtn.classList.remove('text-primary-container');
        navBtn.querySelector('span:last-child')?.classList.remove('font-semibold');
      }
    }
  });

  if (tabName === 'memory') {
    loadSessionHistory();
  } else if (tabName === 'system') {
    testBackendHealth();
  }
}

// -------------------------------------------------------------
// BACKEND HEALTH & TELEMETRY
// -------------------------------------------------------------
async function testBackendHealth() {
  const dot = document.getElementById('connectionBadgeDot');
  const text = document.getElementById('connectionBadgeText');
  const subtitle = document.getElementById('headerSubtitle');
  const telemetryProv = document.getElementById('telemetryProvider');
  const pre = document.getElementById('systemDiagnosticsPre');
  const timestamp = document.getElementById('healthTimestamp');
  const specModel = document.getElementById('specModelName');

  const startTime = performance.now();

  try {
    const resp = await fetch(`${state.backendUrl}/health`, { method: 'GET' });
    const latency = Math.round(performance.now() - startTime);

    if (resp.ok) {
      const data = await resp.json();

      if (dot) {
        dot.className = 'w-2 h-2 rounded-full bg-primary-container animate-pulse';
      }
      if (text) {
        text.textContent = 'ONLINE';
        text.className = 'font-mono text-[11px] text-primary tracking-wider uppercase font-semibold';
      }
      if (subtitle) {
        subtitle.textContent = `${data.llm_provider.toUpperCase()} (${data.llm_model}) • ${latency}ms`;
      }
      if (telemetryProv) {
        telemetryProv.textContent = `Provider: ${data.llm_provider} (${data.llm_model})`;
      }
      if (specModel) {
        specModel.textContent = data.llm_model;
      }
      if (pre) {
        pre.textContent = JSON.stringify(data, null, 2);
      }
      if (timestamp) {
        timestamp.textContent = new Date().toLocaleTimeString();
      }

      document.getElementById('telemetryLatency').textContent = `${latency}ms`;
      return true;
    } else {
      throw new Error(`HTTP ${resp.status}`);
    }
  } catch (err) {
    if (dot) dot.className = 'w-2 h-2 rounded-full bg-error animate-pulse';
    if (text) {
      text.textContent = 'OFFLINE';
      text.className = 'font-mono text-[11px] text-error tracking-wider uppercase font-semibold';
    }
    if (subtitle) subtitle.textContent = 'Could not reach Brain';
    if (pre) pre.textContent = `Connection Error: ${err.message}\nEnsure backend is running at ${state.backendUrl}`;
    return false;
  }
}

// -------------------------------------------------------------
// CHAT & MESSAGING
// -------------------------------------------------------------
function insertPrompt(text) {
  const input = document.getElementById('commandInput');
  if (input) {
    input.value = text;
    input.focus();
    playTone('click');
  }
}

function scrollToBottom() {
  const chatStream = document.getElementById('chatStream');
  if (chatStream) {
    chatStream.scrollTop = chatStream.scrollHeight;
  }
}

function appendUserBubble(message) {
  const emptyHero = document.getElementById('emptyStateHero');
  if (emptyHero) emptyHero.style.display = 'none';

  const stream = document.getElementById('chatStream');
  const bubble = document.createElement('div');
  bubble.className = 'flex flex-col items-end gap-1.5 ml-auto max-w-[88%] animate-fade-in';

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  bubble.innerHTML = `
    <div class="flex items-center gap-1 bg-surface-container-high px-2 py-1 rounded-full text-on-surface-variant font-mono text-[11px]">
      <div class="flex items-end gap-0.5 h-3 px-0.5">
        <span class="w-0.5 bg-secondary rounded-full wave-bar-1"></span>
        <span class="w-0.5 bg-secondary rounded-full wave-bar-3"></span>
        <span class="w-0.5 bg-secondary rounded-full wave-bar-2"></span>
      </div>
      <span class="material-symbols-outlined text-[12px] text-secondary">graphic_eq</span>
      <span>${state.deviceId.toUpperCase()}</span>
    </div>
    <div class="p-3.5 rounded-xl rounded-tr-none bg-surface-container-highest text-on-surface shadow-md border border-outline-variant/30">
      <p class="font-body text-sm leading-relaxed">${escapeHtml(message)}</p>
    </div>
    <span class="font-mono text-[10px] text-outline px-1">${timeStr}</span>
  `;

  stream.appendChild(bubble);
  scrollToBottom();
}

function appendTypingIndicator() {
  const stream = document.getElementById('chatStream');
  const indicator = document.createElement('div');
  indicator.id = 'typingIndicator';
  indicator.className = 'flex items-start gap-2 mr-auto max-w-[94%] animate-pulse';

  indicator.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-surface-container-high flex items-center justify-center shrink-0 mt-1 border border-primary/30">
      <span class="material-symbols-outlined text-primary text-[18px] animate-spin">smart_toy</span>
    </div>
    <div class="p-3 rounded-xl rounded-tl-none bg-surface-container border border-primary/20 text-primary font-mono text-xs flex items-center gap-2 shadow-md">
      <span>JARVIS NEURAL CORE THINKING</span>
      <span class="flex gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-primary-container animate-ping"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-primary-container animate-ping" style="animation-delay: 0.2s"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-primary-container animate-ping" style="animation-delay: 0.4s"></span>
      </span>
    </div>
  `;

  stream.appendChild(indicator);
  scrollToBottom();
  return indicator;
}

function appendAssistantBubble(content, meta = {}) {
  const stream = document.getElementById('chatStream');
  const bubble = document.createElement('div');
  bubble.className = 'flex items-start gap-2 mr-auto max-w-[94%]';

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const provider = meta.provider || 'gemini';
  const historyTurns = meta.history_count !== undefined ? `${meta.history_count} context turn(s)` : '';
  const latency = meta.latency ? ` • ${meta.latency}s` : '';

  // Render markdown if marked is loaded
  let formattedHtml = escapeHtml(content);
  if (typeof marked !== 'undefined' && marked.parse) {
    try {
      formattedHtml = marked.parse(content);
    } catch (e) {
      console.warn('Markdown parsing error:', e);
    }
  }

  bubble.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-surface-container-high flex items-center justify-center shrink-0 mt-1 border border-primary/40 shadow-sm">
      <span class="material-symbols-outlined text-primary text-[18px]">smart_toy</span>
    </div>
    <div class="flex flex-col gap-1.5 min-w-0 flex-1">
      <div class="p-3.5 rounded-xl rounded-tl-none bg-surface-container text-on-surface shadow-md border border-primary-container/20 flex flex-col gap-2">
        <div class="flex items-center justify-between border-b border-surface-container-high pb-1.5 text-xs font-mono">
          <span class="text-primary font-bold tracking-wider uppercase flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-primary-container"></span>
            J.A.R.V.I.S. // EXEC
          </span>
          <span class="text-on-surface-variant text-[11px] truncate max-w-[180px]">${provider}</span>
        </div>
        <div class="prose-code font-body text-sm leading-relaxed overflow-hidden">
          ${formattedHtml}
        </div>
      </div>
      <div class="flex items-center justify-between font-mono text-[10px] text-outline px-1">
        <span>${timeStr}${latency}</span>
        <span class="text-secondary">${historyTurns}</span>
      </div>
    </div>
  `;

  stream.appendChild(bubble);

  // Apply highlight.js to code blocks
  if (typeof hljs !== 'undefined') {
    bubble.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }

  // Add copy buttons to pre blocks
  bubble.querySelectorAll('pre').forEach((pre) => {
    if (!pre.querySelector('.copy-code-btn')) {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-code-btn float-right px-2 py-0.5 mb-1 rounded bg-surface-container-high hover:bg-surface-container-highest text-[10px] font-mono text-primary transition-colors border border-outline-variant/30';
      copyBtn.textContent = 'Copy';
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(pre.innerText.replace(/^Copy\n/, ''));
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
      };
      pre.insertBefore(copyBtn, pre.firstChild);
    }
  });

  scrollToBottom();
}

async function sendChatMessage(presetText = null) {
  const input = document.getElementById('commandInput');
  const message = (presetText || input?.value || '').trim();

  if (!message || state.isProcessing) return;

  state.isProcessing = true;
  if (input && !presetText) input.value = '';

  appendUserBubble(message);
  playTone('send');

  const typingIndicator = appendTypingIndicator();
  const startTime = performance.now();

  try {
    const payload = {
      message: message,
      session_id: state.currentSession,
      device_id: state.deviceId
    };

    const resp = await fetch(`${state.backendUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const elapsedSeconds = ((performance.now() - startTime) / 1000).toFixed(2);
    typingIndicator.remove();

    if (resp.ok) {
      const data = await resp.json();
      data.latency = elapsedSeconds;
      appendAssistantBubble(data.response, data);
      playTone('receive');

      // Update telemetry
      document.getElementById('telemetryHistoryCount').textContent = `Context: ${data.history_count} turn(s)`;
      document.getElementById('telemetryLatency').textContent = `${elapsedSeconds}s`;
    } else {
      const errText = await resp.text();
      appendAssistantBubble(`**Connection Alert**: Received HTTP ${resp.status}\n\`\`\`\n${errText}\n\`\`\``);
    }
  } catch (err) {
    typingIndicator?.remove();
    appendAssistantBubble(`**Neural Link Disconnected**: Could not reach backend at \`${state.backendUrl}\`.\n\n*Please ensure the FastAPI server is running with:* \`python -m uvicorn backend.app.main:app --reload --port 8000\``);
  } finally {
    state.isProcessing = false;
    input?.focus();
  }
}

// -------------------------------------------------------------
// SESSION & MEMORY MANAGEMENT
// -------------------------------------------------------------
function changeSession(newSession) {
  if (!newSession || newSession === state.currentSession) return;
  state.currentSession = newSession;
  localStorage.setItem('jarvis_session_id', state.currentSession);
  updateSessionHeaders();
  clearChatView();
  loadSessionHistory();
  playTone('click');
}

function createNewSession() {
  const input = document.getElementById('newSessionInput');
  const sessionName = (input?.value || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  if (!sessionName) return;

  const selector = document.getElementById('sessionSelector');
  if (selector) {
    let exists = false;
    for (let opt of selector.options) {
      if (opt.value === sessionName) { exists = true; break; }
    }
    if (!exists) {
      const opt = document.createElement('option');
      opt.value = sessionName;
      opt.textContent = sessionName;
      selector.appendChild(opt);
    }
    selector.value = sessionName;
  }

  input.value = '';
  changeSession(sessionName);
}

function updateSessionHeaders() {
  const header = document.getElementById('activeSessionHeader');
  const transcriptSpan = document.getElementById('transcriptSessionId');
  const selector = document.getElementById('sessionSelector');

  if (header) header.textContent = state.currentSession;
  if (transcriptSpan) transcriptSpan.textContent = state.currentSession;
  if (selector) selector.value = state.currentSession;
}

function clearChatView() {
  const stream = document.getElementById('chatStream');
  if (stream) {
    stream.innerHTML = '';
    const hero = document.getElementById('emptyStateHero');
    if (hero) {
      hero.style.display = 'flex';
      stream.appendChild(hero);
    }
  }
}

async function loadSessionHistory() {
  const tbody = document.getElementById('memoryTableBody');
  const totalCountElem = document.getElementById('memTotalCount');

  try {
    const resp = await fetch(`${state.backendUrl}/history/${state.currentSession}`);
    if (resp.ok) {
      const data = await resp.json();
      const messages = data.messages || [];

      if (totalCountElem) totalCountElem.textContent = messages.length;

      // Populate memory table
      if (tbody) {
        if (messages.length === 0) {
          tbody.innerHTML = `<p class="text-outline text-center py-6">No transcript history stored for session '${state.currentSession}'.</p>`;
        } else {
          tbody.innerHTML = messages.map(m => {
            const isUser = m.role === 'user';
            const roleColor = isUser ? 'text-primary' : 'text-secondary';
            const bgClass = isUser ? 'bg-surface-container-lowest' : 'bg-surface-container-low';
            const time = m.created_at ? new Date(m.created_at).toLocaleTimeString() : '';

            return `
              <div class="p-2.5 rounded-lg ${bgClass} border border-outline-variant/20 flex flex-col gap-1">
                <div class="flex items-center justify-between text-[11px]">
                  <span class="${roleColor} font-bold uppercase tracking-wider">#${m.id} [${m.role}]</span>
                  <span class="text-outline text-[10px]">${time} • ${m.device_id || 'unknown'}</span>
                </div>
                <p class="text-on-surface font-body text-xs whitespace-pre-wrap">${escapeHtml(m.content)}</p>
              </div>
            `;
          }).join('');
        }
      }

      // Populate chat view on initial boot if empty
      const stream = document.getElementById('chatStream');
      if (stream && stream.children.length <= 1 && messages.length > 0) {
        const hero = document.getElementById('emptyStateHero');
        if (hero) hero.style.display = 'none';

        messages.forEach(m => {
          if (m.role === 'user') {
            appendUserBubble(m.content);
          } else {
            appendAssistantBubble(m.content, { provider: 'sqlite-transcript' });
          }
        });
      }
    }
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<p class="text-error text-center py-4">Failed to load memory: ${err.message}</p>`;
    }
  }
}

async function clearSessionHistory() {
  if (!confirm(`Are you sure you want to purge all conversation memory for session '${state.currentSession}'?`)) {
    return;
  }

  try {
    const resp = await fetch(`${state.backendUrl}/history/${state.currentSession}`, {
      method: 'DELETE'
    });

    if (resp.ok) {
      playTone('clear');
      clearChatView();
      loadSessionHistory();
      document.getElementById('telemetryHistoryCount').textContent = 'Context: 0 turns';
    } else {
      alert(`Error clearing history: HTTP ${resp.status}`);
    }
  } catch (err) {
    alert(`Connection error: ${err.message}`);
  }
}

// -------------------------------------------------------------
// ACTIONS TAB SIMULATION
// -------------------------------------------------------------
async function runHealthProbeAction() {
  const consoleLog = document.getElementById('actionsConsoleLog');
  const timestamp = document.getElementById('consoleTimestamp');

  if (consoleLog) {
    consoleLog.textContent = `[PROBE]: Pinging ${state.backendUrl}/health...\n`;
    const start = performance.now();
    try {
      const resp = await fetch(`${state.backendUrl}/health`);
      const elapsed = Math.round(performance.now() - start);
      const data = await resp.json();
      consoleLog.textContent += `[STATUS]: HTTP 200 OK (${elapsed}ms)\n[PAYLOAD]: ${JSON.stringify(data, null, 2)}\n[RESULT]: Subsystems nominal.`;
    } catch (e) {
      consoleLog.textContent += `[FAILURE]: ${e.message}\n`;
    }
  }
  if (timestamp) timestamp.textContent = new Date().toLocaleTimeString();
  playTone('receive');
}

// -------------------------------------------------------------
// VOICE INPUT (WEB SPEECH API)
// -------------------------------------------------------------
function setupVoiceRecognition() {
  const micBtn = document.getElementById('arcMicBtn');
  const micIcon = document.getElementById('micIcon');
  const micInner = document.getElementById('micInnerCircle');
  const pingAnim = document.getElementById('micPingAnim');
  const input = document.getElementById('commandInput');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    if (micBtn) {
      micBtn.title = 'Speech Recognition not supported in this browser';
      micBtn.classList.add('opacity-50');
    }
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    state.isRecording = true;
    if (micInner) micInner.className = 'absolute inset-0.5 rounded-full bg-error-container flex items-center justify-center';
    if (micIcon) {
      micIcon.textContent = 'graphic_eq';
      micIcon.className = 'material-symbols-outlined text-error text-[20px] animate-pulse';
    }
    if (pingAnim) pingAnim.className = 'absolute inset-0 bg-error/30 rounded-full animate-ping opacity-80';
    playTone('click');
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    if (input) {
      input.value = transcript;
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
    if (input && input.value.trim()) {
      sendChatMessage();
    }
  };

  function stopRecording() {
    state.isRecording = false;
    if (micInner) micInner.className = 'absolute inset-0.5 rounded-full bg-surface-container flex items-center justify-center';
    if (micIcon) {
      micIcon.textContent = 'mic';
      micIcon.className = 'material-symbols-outlined text-primary-container text-[20px]';
    }
    if (pingAnim) pingAnim.className = 'absolute inset-0 bg-primary-container/20 rounded-full animate-ping opacity-60';
  }

  if (micBtn) {
    micBtn.addEventListener('click', () => {
      if (state.isRecording) {
        recognition.stop();
      } else {
        try {
          recognition.start();
        } catch (err) {
          console.warn('Recognition start failed:', err);
        }
      }
    });
  }
}

// -------------------------------------------------------------
// SETTINGS
// -------------------------------------------------------------
function saveBackendUrl() {
  const input = document.getElementById('backendUrlInput');
  if (!input) return;
  const url = input.value.trim().replace(/\/+$/, '');
  if (url) {
    state.backendUrl = url;
    localStorage.setItem('jarvis_backend_url', url);
    playTone('click');
    testBackendHealth();
    loadSessionHistory();
    alert(`Backend URL updated to: ${url}`);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// -------------------------------------------------------------
// INITIALIZATION
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  // Input bindings
  const sendBtn = document.getElementById('sendBtn');
  const commandInput = document.getElementById('commandInput');
  const backendInput = document.getElementById('backendUrlInput');

  if (sendBtn) {
    sendBtn.addEventListener('click', () => sendChatMessage());
  }

  if (commandInput) {
    commandInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }

  if (backendInput) {
    backendInput.value = state.backendUrl;
  }

  // Audio icon state
  const audioIcon = document.getElementById('audioIcon');
  if (audioIcon) {
    audioIcon.textContent = state.audioEnabled ? 'volume_up' : 'volume_off';
  }

  updateSessionHeaders();
  setupVoiceRecognition();
  testBackendHealth();
  loadSessionHistory();

  // Periodic heartbeat polling every 10 seconds
  setInterval(testBackendHealth, 10000);
});
