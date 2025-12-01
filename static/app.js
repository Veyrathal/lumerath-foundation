// static/js/app.js
import { API_BASE, PROJECT_ID, CHAT_ID, X_USER_ID } from './config.js';

const $ = (q) => document.querySelector(q);

// hydrate from memory on load (nice to show goals / context)
async function loadMemory() {
  const r = await fetch(`${API_BASE}/memory/${PROJECT_ID}`, {
    headers: { 'x-user-id': X_USER_ID }
  });
  if (!r.ok) return;
  const data = await r.json();
  // put whatever you stored under "goals" into a simple view:
  const goals = data?.goals?.list || [];
  const box = $('#memoryBox');
  if (box) box.textContent = goals.length ? goals.join(' • ') : '(no goals yet)';
}

// send a chat message to the backend
async function sendMessage(text) {
  if (!text.trim()) return;
  const r = await fetch(`${API_BASE}/chats/${CHAT_ID}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-user-id': X_USER_ID
    },
    body: JSON.stringify({ message: text })
  });
  const j = await r.json().catch(() => ({}));
  // optional: show status
  const log = $('#chatLog');
  if (log) {
    const li = document.createElement('div');
    li.textContent = `→ ${text}`;
    log.appendChild(li);
    if (j.reply) {
      const ai = document.createElement('div');
      ai.textContent = `← ${j.reply}`;
      log.appendChild(ai);
    }
  }
  $('#chatInput').value = '';
}

window.addEventListener('DOMContentLoaded', () => {
  // hook up UI
  const btn = $('#sendBtn');
  if (btn) btn.addEventListener('click', () => sendMessage($('#chatInput').value));
  loadMemory();
});
