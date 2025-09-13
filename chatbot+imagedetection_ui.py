# krishi_sevak_app.py
from flask import Flask, request, jsonify, Response, redirect, url_for, session
from functools import wraps
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import os
import hashlib
import time

# ---------------------------
# KrishiSevak single-file Flask app
# - Original UI preserved
# - Left sidebar (ChatGPT style) with conversations
# - New Chat opens a new conversation (does not delete history)
# - Delete individual conversations
# - Persistent per-user conversations (in-memory demo)
# - Smooth light/dark morph animation added
# ---------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-demo-key")

DEMO_USER = "farmer"
DEMO_PASS_HASH = hashlib.sha256("password123".encode()).hexdigest()

# Knowledge base (unchanged)
knowledge_base = {
    "corn": {"common rust": "Cause: Fungus (Puccinia sorghi). Symptoms: reddish-brown pustules on leaves. Control: resistant varieties, fungicides.",
             "gray leaf spot": "Cause: Fungus (Cercospora zeae-maydis). Symptoms: gray rectangular lesions. Control: resistant hybrids, fungicides.",
             "leaf blight": "Cause: Fungus (Exserohilum turcicum). Symptoms: cigar-shaped lesions. Control: resistant hybrids, fungicides.",
             "healthy": "Green leaves, no lesions, normal growth."},
    "potato": {"early blight": "Cause: Fungus (Alternaria solani). Symptoms: concentric dark spots. Control: crop rotation, fungicides.",
               "late blight": "Cause: Oomycete (Phytophthora infestans). Symptoms: water-soaked lesions, white mold. Control: resistant varieties, fungicides.",
               "healthy": "Green leaves, no dark spots."},
    "rice": {"brown spot": "Cause: Fungus (Bipolaris oryzae). Symptoms: brown circular spots with yellow halo. Control: seed treatment, fungicides.",
             "hispa": "Cause: Insect (Dicladispa armigera). Symptoms: scraping on leaves, small holes. Control: insecticides, resistant varieties.",
             "leaf blast": "Cause: Fungus (Magnaporthe oryzae). Symptoms: diamond-shaped lesions. Control: resistant varieties, fungicides.",
             "healthy": "No lesions, normal green leaves."},
    "wheat": {"brown rust": "Cause: Fungus (Puccinia triticina). Symptoms: orange-brown pustules. Control: resistant varieties, fungicides.",
              "yellow rust": "Cause: Fungus (Puccinia striiformis). Symptoms: yellow stripes of pustules. Control: resistant varieties, fungicides.",
              "healthy": "Uniform green leaves, no pustules."}
}

# Load model (same checkpoint). If unavailable the predict endpoint will error gracefully.
try:
    processor = AutoImageProcessor.from_pretrained("wambugu71/crop_leaf_diseases_vit")
    model = AutoModelForImageClassification.from_pretrained("wambugu71/crop_leaf_diseases_vit")
except Exception as e:
    print("Warning: failed to load model (predict disabled):", e)
    processor = None
    model = None

# Helpers
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            return jsonify({"error": "authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# In-memory per-user conversations storage (demo)
# Structure:
# user_conversations = {
#   "username": {
#       "next_id": 1,
#       "conversations": [
#           { "id": 1, "title": "New Chat", "created_at": 1234567890.0, "messages":[{"role":"user","message":"..."}, {"role":"bot","message":"..."}] },
#           ...
#       ]
#   },
#   ...
# }
# ---------------------------
user_conversations = {}

# ---------------------------
# HTML templates (LOGIN + DASHBOARD)
# I've preserved your original UI and added sidebar JS to manage conversations.
# Smooth transition/morph for light/dark: small CSS + JS helper
# ---------------------------

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>🌱 KrishiSevak — Login</title>
  <style>
    :root { --leaf-color: "🍃"; }
    body { font-family: 'Segoe UI', sans-serif; margin:0; padding:0; min-height:100vh; display:flex; justify-content:center; align-items:center; color:#f9fafb;
           background: linear-gradient(270deg, #0f172a, #166534, #065f46, #22c55e); background-size:600% 600%; animation:gradientShift 15s ease infinite; overflow-x:hidden; transition: background 700ms ease, color 400ms ease; }
    @keyframes gradientShift { 0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%} }
    .card { width:420px; max-width:90%; background:rgba(255,255,255,0.06); backdrop-filter: blur(12px); border-radius:16px; padding:28px; box-shadow:0 12px 40px rgba(2,6,23,0.6); border:1px solid rgba(255,255,255,0.08); transition: background 600ms ease, transform 300ms ease; }
    h2{margin:0 0 8px 0;font-size:1.6rem;background:linear-gradient(90deg,#22c55e,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
    .input{width:100%;padding:12px;border-radius:10px;border:none;margin-top:10px;background:rgba(255,255,255,0.06);color:#e6fffa;}
    .btn{width:100%;padding:12px;border-radius:10px;border:none;margin-top:14px;background:linear-gradient(135deg,#22c55e,#4ade80);color:#062e16;font-weight:700;}
    .floating-leaf{position:fixed;top:-50px;font-size:1.5rem;animation:fall linear forwards;z-index:9999;pointer-events:none;}
    @keyframes fall{0%{transform:translateY(-50px) rotate(0deg);opacity:1}100%{transform:translateY(110vh) rotate(360deg);opacity:0}}
    .top-right{position:absolute;top:18px;right:18px;color:rgba(255,255,255,0.8);}
  </style>
</head>
<body>
  <div class="top-right">🌾 KrishiSevak</div>
  <div class="card" role="main">
    <h2>Welcome back</h2>
    <p style="color:#d1d5db;margin-top:6px;margin-bottom:16px;">Sign in to access your Smart Crop Assistant</p>
    <form method="POST" action="/login">
      <input class="input" name="username" placeholder="Username" required>
      <input class="input" name="password" type="password" placeholder="Password" required>
      <button class="btn" type="submit">Sign in</button>
    </form>
    <p style="margin-top:12px;color:#9ca3af;font-size:0.9rem;">Demo: user <strong>farmer</strong> / pass <strong>password123</strong></p>
  </div>
  <script>
    const leafEmojis = ["🍃","🍂","🌿"];
    const leafColors = ["#22c55e","#a3e635","#facc15","#f97316"];
    function createLeaf(){const leaf=document.createElement("div");leaf.classList.add("floating-leaf");const emoji=leafEmojis[Math.floor(Math.random()*leafEmojis.length)];leaf.textContent=emoji;leaf.style.color=leafColors[Math.floor(Math.random()*leafColors.length)];leaf.style.left=Math.random()*100+"vw";leaf.style.fontSize=(Math.random()*20+15)+"px";leaf.style.animationDuration=(Math.random()*5+5)+"s";document.body.appendChild(leaf);setTimeout(()=>leaf.remove(),10000);}
    setInterval(createLeaf,1500);
  </script>
</body>
</html>
'''

# Dashboard: original UI preserved; JS updated to use conversation endpoints.
# Added smooth morph transition for theme switching.
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🌱 Smart Crop Assistant</title>
<style>
:root { --leaf-color: "🍃"; --bg-start: #0f172a; --bg-mid: #166534; --bg-end: #22c55e; --glass: rgba(255,255,255,0.08); --text: #f9fafb; --muted: #9ca3af; }
html,body { height:100%; }
body { font-family: 'Segoe UI', sans-serif; margin:0; padding:0; min-height:100vh; display:flex; color:var(--text);
       background: linear-gradient(270deg, var(--bg-start), #166534, #065f46, var(--bg-end)); background-size:600% 600%; animation:gradientShift 15s ease infinite; overflow:hidden;
       transition: background 700ms cubic-bezier(.2,.9,.3,1), color 400ms ease; }
@keyframes gradientShift { 0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%} }
.app-layout{display:flex; width:100%; height:100vh; gap:1rem; padding:1rem; box-sizing:border-box; align-items:stretch;}

/* Sidebar */
.sidebar{width:300px; background:rgba(0,0,0,0.28); border-radius:16px; padding:16px; box-sizing:border-box; display:flex; flex-direction:column; gap:10px; color:#e6fffa; overflow:auto; transition: background 500ms ease, transform 300ms ease;}
.sidebar .top { display:flex; justify-content:space-between; align-items:center; }
.sidebar h3{margin:0;}
.primary-btn{padding:8px 10px;border-radius:8px;border:none;background:linear-gradient(135deg,#22c55e,#4ade80);color:#062e16;font-weight:700;cursor:pointer; transition: transform 160ms ease; }
.primary-btn:active{ transform: scale(.98); }
.search { padding:8px; border-radius:8px; border:none; background:rgba(255,255,255,0.04); color:#e6fffa; width:100%; box-sizing:border-box; transition: background 300ms ease; }
.history-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;}
.history-item{padding:10px;border-radius:8px;background:rgba(255,255,255,0.03);display:flex;justify-content:space-between;align-items:center;cursor:pointer; transition: background 200ms ease;}
.history-item:hover{background:rgba(255,255,255,0.06);}
.history-title{flex:1; margin-right:8px; color:#e6fffa;}

/* Main (original container preserved) */
.container{flex:1; max-width:100%; background: var(--glass); backdrop-filter: blur(16px); border-radius:24px; padding:2rem; box-shadow:0 8px 40px rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.2); overflow:auto; transition: background 600ms ease, border-color 600ms ease;}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem;}
.logo{font-size:1.5rem;font-weight:bold;color:#22c55e;text-shadow:0 0 8px #22c55e;}
.toggle-btn{background:none;border:none;font-size:1.8rem;cursor:pointer; transition: transform 180ms ease; }
.toggle-btn:hover{ transform: scale(1.08) rotate(6deg); }
.user-wrap{display:flex;gap:12px;align-items:center;}
.user-name{color:#bbf7d0;font-weight:600;}
.logout-btn{padding:6px 12px;border-radius:8px;border:none;cursor:pointer;background:transparent;color:#d1fae5;border:1px solid rgba(255,255,255,0.12); transition: background 200ms ease; }

h1{text-align:center;font-size:2.2rem;background:linear-gradient(90deg,#22c55e,#4ade80,#a7f3d0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.5rem;}
.subtitle{text-align:center;font-size:1.1rem;color:#d1d5db;margin-bottom:2rem;}

.upload-section{display:flex;flex-direction:column;align-items:center;margin:1.5rem 0;}
.upload-box{border:2px dashed rgba(34,197,94,0.8);border-radius:20px;padding:2.5rem;text-align:center;cursor:pointer;background:rgba(34,197,94,0.05);transition:all 0.3s ease;max-width:500px;width:100%;animation:glowPulse 2.5s infinite;}
.preview-img{margin-top:1rem;max-width:300px;border-radius:16px;}
@keyframes glowPulse {0%{box-shadow:0 0 5px rgba(34,197,94,0.3),0 0 15px rgba(34,197,94,0.2);}50%{box-shadow:0 0 20px rgba(34,197,94,0.6),0 0 40px rgba(34,197,94,0.4);}100%{box-shadow:0 0 5px rgba(34,197,94,0.3),0 0 15px rgba(34,197,94,0.2);}}

.prediction{background:rgba(16,185,129,0.1);border:1px solid #10b981;padding:1rem;border-radius:16px;margin-top:1rem;color:#a7f3d0;box-shadow:inset 0 0 20px rgba(16,185,129,0.3);max-width:500px;text-align:center;}
.loading{display:flex;justify-content:center;align-items:center;gap:10px;font-size:2rem;animation:fadeIn 0.5s ease;}
.loading span{display:inline-block;animation:leafBounce 1.2s infinite;}
.loading span:nth-child(2){animation-delay:0.2s;}
.loading span:nth-child(3){animation-delay:0.4s;}
@keyframes leafBounce{0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-10px) rotate(20deg);}}

/* chat */
.card{margin-top:2rem;padding:1.5rem;border-radius:20px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);position:relative;}
.chat-box{max-height:300px;overflow-y:auto;margin-top:1rem;padding:0.5rem;display:flex;flex-direction:column;gap:8px;}
.chat-msg{padding:10px 16px;margin:10px 0;border-radius:16px;max-width:80%;font-size:0.95rem;animation:fadeIn 0.5s ease;position:relative;}
.chat-user{background:linear-gradient(135deg,#22c55e,#16a34a);color:white;margin-left:auto;text-align:right;box-shadow:0 0 12px rgba(34,197,94,0.5);}
.chat-bot{background:rgba(255,255,255,0.15);color:#f9fafb;margin-right:auto;}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}

.chat-input{width:100%;padding:12px;border-radius:12px;border:none;margin-top:0.8rem;background:rgba(255,255,255,0.1);color:white;font-size:1rem;}
.btn{margin-top:1rem;padding:12px 28px;border:none;border-radius:12px;background:linear-gradient(135deg,#22c55e,#4ade80);color:white;cursor:pointer;font-size:1rem;transition:transform 0.3s ease,box-shadow 0.3s ease;}
.btn:hover{transform:scale(1.05);box-shadow:0 0 20px rgba(34,197,94,0.6);}

.floating-leaf{position:fixed;top:-50px;font-size:1.5rem;animation:fall linear forwards;z-index:9999;pointer-events:none;}
@keyframes fall{0%{transform:translateY(-50px) rotate(0deg);opacity:1}100%{transform:translateY(110vh) rotate(360deg);opacity:0}}

footer{margin-top:2rem;text-align:center;font-size:0.85rem;color:#9ca3af;}

/* DARK THEME (morph) */
body.dark {
  --bg-start: #0b1220;
  --bg-mid: #0f172a;
  --bg-end: #064e3b;
  --glass: rgba(255,255,255,0.03);
  --text: #eef6ec;
  --muted: #9ca3af;
}
</style>
</head>
<body>
  <div class="app-layout">
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
      <div class="top">
        <h3>🌿 Chats</h3>
        <form method="POST" action="/logout" style="margin:0;">
          <button class="primary-btn" type="submit" title="Logout">Logout</button>
        </form>
      </div>
      <div>
        <button class="primary-btn" onclick="createConversation()">+ New Chat</button>
      </div>
      <input class="search" id="sidebar-search" placeholder="Search chats or messages...">
      <div style="font-size:0.9rem;color:#c7f9d9;margin-top:6px;">History</div>
      <ul class="history-list" id="history-list"></ul>
    </div>

    <!-- Main -->
    <div class="container" id="main-container">
      <div class="topbar">
        <div class="logo">🌾 KrishiSevak</div>
        <div class="user-wrap">
          <button id="mode-toggle" class="toggle-btn" aria-label="Toggle theme">🌱</button>
          <div class="user-name">__USERNAME__</div>
        </div>
      </div>

      <h1>Smart Crop Assistant</h1>
      <p class="subtitle">AI-Powered Farming • Disease Detection • Smart Chatbot</p>

      <div class="upload-section">
        <label for="file-upload" class="upload-box">
          🌿 Drop your crop leaf image here or click to upload
          <input id="file-upload" type="file" accept="image/*">
        </label>
        <div id="preview"></div>
        <div id="result" class="prediction" style="display:none;"></div>
      </div>

      <div class="card">
        <h3 id="chat-title">🍃 Ask Krishi Bot</h3>
        <div id="chat-box" class="chat-box"></div>
        <input id="chat-input" class="chat-input" placeholder="Type your farming question...">
        <button class="btn" onclick="sendMessage()">Send</button>
      </div>

      <div class="card">
        <h3>🔮 Future Features</h3>
        <ul>
          <li>🌦 Real-time weather + disease alerts</li>
          <li>📊 AI-based yield + price prediction</li>
          <li>🎤 Voice-enabled farmer assistant</li>
          <li>🛰 Satellite + IoT crop monitoring</li>
        </ul>
      </div>

      <footer>© 2025 Krishi Sevak | Built with ⚡ Future Tech for Farmers (SIH)</footer>
    </div>
  </div>

<script>
  // ---- Smooth theme morph helper ----
  // When toggling theme we add a short-lived 'theme-transition' to enable smooth CSS transitions for background/colors
  function enableSmoothTransitionOnce() {
    document.documentElement.classList.add('theme-transition-temp');
    // Ensure CSS transition properties are applied by adding a style element if needed:
    if (!document.getElementById('theme-transition-styles')) {
      const style = document.createElement('style');
      style.id = 'theme-transition-styles';
      style.innerHTML = `
        .theme-transition-temp * {
          transition: background 700ms cubic-bezier(.2,.9,.3,1), color 500ms ease, border-color 600ms ease !important;
        }
      `;
      document.head.appendChild(style);
    }
    clearTimeout(window._themeTransitionTO);
    window._themeTransitionTO = setTimeout(() => {
      document.documentElement.classList.remove('theme-transition-temp');
    }, 800);
  }

  // Dark mode toggle (original but with smooth morph)
  const toggleBtn = document.getElementById("mode-toggle");
  function updateLeafIcon(){ toggleBtn.textContent=document.body.classList.contains("dark")?"🍃":"🌱"; }
  updateLeafIcon();
  toggleBtn && toggleBtn.addEventListener("click", ()=>{
    enableSmoothTransitionOnce();
    document.body.classList.toggle("dark");
    updateLeafIcon();
  });

  // Floating leaves (original)
  const leafEmojis=["🍃","🍂","🌿"];
  const leafColors=["#22c55e","#a3e635","#facc15","#f97316"];
  function createLeaf(){ const leaf=document.createElement("div"); leaf.classList.add("floating-leaf"); const emoji=leafEmojis[Math.floor(Math.random()*leafEmojis.length)]; leaf.textContent=emoji; leaf.style.color=leafColors[Math.floor(Math.random()*leafColors.length)]; leaf.style.left=Math.random()*100+"vw"; leaf.style.fontSize=(Math.random()*20+15)+"px"; leaf.style.animationDuration=(Math.random()*5+5)+"s"; document.body.appendChild(leaf); setTimeout(()=>leaf.remove(),10000); }
  setInterval(createLeaf,1500);

  // File upload & prediction (original behavior)
  const fileInput = document.getElementById("file-upload");
  const previewDiv = document.getElementById("preview");
  const resultDiv = document.getElementById("result");
  fileInput && fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => { previewDiv.innerHTML = `<img src="${e.target.result}" class="preview-img">`; };
    reader.readAsDataURL(file);

    resultDiv.style.display = "block";
    resultDiv.innerHTML = `<div class="loading"><span>🍃</span><span>🍃</span><span>🍃</span></div><p>Analyzing leaf health...</p>`;

    const formData = new FormData(); formData.append("file", file);
    const response = await fetch("/predict", { method: "POST", body: formData });
    if (response.status === 401 || response.status === 403) { resultDiv.innerHTML = '<p>Please login to use prediction.</p>'; return; }
    const data = await response.json();
    resultDiv.innerHTML = data.error ? `<p>Error: ${data.error}</p>` : `<h3>🩺 Prediction: ${data.prediction}</h3>`;
  });

  // ---------------- Conversation & Sidebar logic ----------------
  let currentConversationId = null;

  // Helper: create a new conversation (server-side)
  async function createConversation() {
    const res = await fetch('/conversations', { method: 'POST' });
    if (res.status === 401) { alert('Please login'); return; }
    const data = await res.json();
    currentConversationId = data.id;
    await refreshSidebar();
    openConversation(currentConversationId);
  }

  // Refresh sidebar list
  async function refreshSidebar() {
    const res = await fetch('/conversations');
    if (res.status === 401) return;
    const data = await res.json(); // list of conv meta
    const list = document.getElementById('history-list');
    list.innerHTML = '';
    if (!data || data.length === 0) {
      list.innerHTML = '<li style="color:#9ca3af;padding:8px;">No conversations yet. Click New Chat.</li>';
      return;
    }
    data.forEach(conv => {
      const li = document.createElement('li');
      li.className = 'history-item';
      const title = document.createElement('div');
      title.className = 'history-title';
      title.textContent = conv.title || ('Chat ' + conv.id);
      title.title = conv.preview || '';
      title.addEventListener('click', () => { openConversation(conv.id); });
      const delBtn = document.createElement('button');
      delBtn.className = 'primary-btn';
      delBtn.style.background = 'transparent';
      delBtn.style.color = '#fca5a5';
      delBtn.style.border = '1px solid rgba(255,255,255,0.08)';
      delBtn.style.padding = '6px 8px';
      delBtn.style.marginLeft = '8px';
      delBtn.textContent = 'Delete';
      delBtn.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        if (!confirm('Delete this conversation? This cannot be undone.')) return;
        await fetch('/conversations/' + conv.id, { method: 'DELETE' });
        if (currentConversationId === conv.id) {
          currentConversationId = null;
          document.getElementById('chat-box').innerHTML = '';
        }
        await refreshSidebar();
      });

      li.appendChild(title);
      li.appendChild(delBtn);
      list.appendChild(li);
    });
  }

  // Open a conversation (load messages)
  async function openConversation(id) {
    currentConversationId = id;
    const res = await fetch('/conversations/' + id);
    if (res.status === 404) { alert('Conversation not found'); return; }
    const data = await res.json();
    // set chat title preview
    document.getElementById('chat-title').textContent = '🍃 ' + (data.title || 'Conversation ' + data.id);
    // render messages
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '';
    for (const m of data.messages) {
      const div = document.createElement('div');
      div.className = 'chat-msg ' + (m.role === 'user' ? 'chat-user' : 'chat-bot');
      div.textContent = m.message;
      chatBox.appendChild(div);
    }
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // Send message to current conversation
  async function sendMessage() {
    if (!currentConversationId) {
      // auto-create conversation if none selected
      await createConversation();
    }
    const inputEl = document.getElementById('chat-input');
    const query = inputEl.value.trim();
    if (!query) return;
    // show user message locally
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="chat-msg chat-user">${escapeHtml(query)}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    inputEl.value = '';

    // post to server to store user msg and get bot reply
    const res = await fetch(`/conversations/${currentConversationId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (res.status === 401) { alert('Please login'); return; }
    const data = await res.json();
    // show typing animation and bot reply
    const botDiv = document.createElement('div');
    botDiv.className = 'chat-msg chat-bot';
    chatBox.appendChild(botDiv);
    let i = 0;
    const text = data.response;
    const typing = setInterval(() => {
      botDiv.textContent = text.slice(0, i++);
      if (i > text.length) {
        clearInterval(typing);
        const randomLeaf = leafEmojis[Math.floor(Math.random() * leafEmojis.length)];
        botDiv.textContent += ' ' + randomLeaf;
        createLeaf();
      }
      chatBox.scrollTop = chatBox.scrollHeight;
    }, 18);

    // refresh sidebar
    await refreshSidebar();
  }

  // Escape HTML helper
  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<"']/g, function(m){ return {'&':'&amp;','<':'&lt;','"':'&quot;',"'":'&#039;'}[m]; });
  }

  // Sidebar search filter
  document.getElementById('sidebar-search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    [...document.querySelectorAll('.history-item')].forEach(li => {
      const txt = li.querySelector('.history-title').textContent.toLowerCase();
      li.style.display = txt.includes(q) ? 'flex' : 'none';
    });
  });

  // On page load: ensure currentConversationId set (open last conversation if any)
  (async function init() {
    await refreshSidebar();
    // open last conv if exists
    const res = await fetch('/conversations');
    if (res.status !== 200) return;
    const convs = await res.json();
    if (convs && convs.length > 0) {
      const last = convs[convs.length - 1];
      openConversation(last.id);
    }
  })();
</script>
</body>
</html>
'''

# ---------------------------
# Server routes for conversations
# ---------------------------

def ensure_user_store(username):
    # Create user store if missing
    if username not in user_conversations:
        user_conversations[username] = {"next_id": 1, "conversations": []}

@app.route('/conversations', methods=['GET', 'POST'])
@login_required
def conversations():
    user = session.get('user')
    ensure_user_store(user)
    store = user_conversations[user]
    if request.method == 'GET':
        # return list of conversations with preview metadata
        out = []
        for conv in store['conversations']:
            preview = ''
            # pick first user message as preview if available, else first bot
            for m in conv['messages']:
                preview = m['message']
                break
            out.append({
                "id": conv['id'],
                "title": conv.get('title') or (preview[:60] if preview else f"Chat {conv['id']}"),
                "preview": preview[:120] if preview else ""
            })
        return jsonify(out)
    else:
        # create new conversation
        cid = store['next_id']
        store['next_id'] += 1
        conv = {"id": cid, "title": "New Chat", "created_at": time.time(), "messages": []}
        store['conversations'].append(conv)
        return jsonify({"id": cid, "title": conv['title']}), 201

@app.route('/conversations/<int:cid>', methods=['GET', 'DELETE'])
@login_required
def conversation_get_delete(cid):
    user = session.get('user')
    ensure_user_store(user)
    store = user_conversations[user]
    conv = next((c for c in store['conversations'] if c['id'] == cid), None)
    if conv is None:
        return jsonify({"error": "not found"}), 404
    if request.method == 'GET':
        return jsonify({"id": conv['id'], "title": conv.get('title'), "messages": conv['messages']})
    else:
        # delete conversation
        store['conversations'] = [c for c in store['conversations'] if c['id'] != cid]
        return jsonify({'status': 'deleted'})

@app.route('/conversations/<int:cid>/message', methods=['POST'])
@login_required
def conversation_message(cid):
    user = session.get('user')
    ensure_user_store(user)
    store = user_conversations[user]
    conv = next((c for c in store['conversations'] if c['id'] == cid), None)
    if conv is None:
        return jsonify({"error": "conversation not found"}), 404
    data = request.get_json() or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({"error": "no query provided"}), 400

    # Append user message
    conv['messages'].append({"role": "user", "message": query, "ts": time.time()})
    # Optionally update title to first user message
    if conv.get('title') == "New Chat":
        conv['title'] = query if len(query) <= 60 else query[:57] + "..."

    # Generate response using knowledge base (same logic as before)
    q_lower = query.lower()
    response = "Sorry, I couldn't find information. Please ask about corn, potato, rice, or wheat diseases."
    for crop, diseases in knowledge_base.items():
        if crop in q_lower:
            for disease, info in diseases.items():
                if disease in q_lower:
                    response = f"🌱 {crop.capitalize()} - {disease.capitalize()}: {info}"
                    break
            else:
                response = f"🌱 {crop.capitalize()} Info: {', '.join(diseases.keys())}"
            break

    # Append bot response
    conv['messages'].append({"role": "bot", "message": response, "ts": time.time()})
    return jsonify({"response": response})

# ---------------------------
# Legacy endpoints kept for compatibility (optional)
# ---------------------------
@app.route('/history', methods=['GET'])
@login_required
def history_all():
    # return full flattened messages of the last conversation for compatibility
    user = session.get('user')
    ensure_user_store(user)
    store = user_conversations[user]
    if not store['conversations']:
        return jsonify([])
    # return messages of last conv
    return jsonify(store['conversations'][-1]['messages'])

# ---------------------------
# Other original routes: index, login, logout, predict
# ---------------------------

@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    html = DASHBOARD_HTML.replace('__USERNAME__', session.get('user'))
    return Response(html, mimetype='text/html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if username == DEMO_USER and hashlib.sha256(password.encode()).hexdigest() == DEMO_PASS_HASH:
            session['user'] = username
            # ensure user conversations
            ensure_user_store(username)
            # if user has no conversations, auto-create one
            if not user_conversations[username]['conversations']:
                # create initial conversation
                user_conversations[username]['conversations'].append({
                    "id": user_conversations[username]['next_id'],
                    "title": "New Chat",
                    "created_at": time.time(),
                    "messages": []
                })
                user_conversations[username]['next_id'] += 1
            return redirect(url_for('index'))
        return Response(LOGIN_HTML + '<script>alert("Invalid credentials")</script>', mimetype='text/html')
    return Response(LOGIN_HTML, mimetype='text/html')

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if model is None or processor is None:
        return jsonify({'error':'model not loaded'}), 500
    file = request.files.get('file')
    if not file:
        return jsonify({'error':'no file'}), 400
    try:
        image = Image.open(file.stream).convert('RGB')
        inputs = processor(images=image, return_tensors='pt')
        with torch.no_grad():
            outputs = model(**inputs)
        logits = outputs.logits
        predicted_class_id = logits.argmax(-1).item()
        label = model.config.id2label[predicted_class_id].lower()
        return jsonify({'prediction': label})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    print("Starting KrishiSevak app on http://127.0.0.1:5000")
    app.run(debug=True)
