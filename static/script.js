document.addEventListener('DOMContentLoaded', function() {
    var navToggle = document.getElementById('navToggle');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            document.querySelector('.nav-links').classList.toggle('open');
        });
    }

    var chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

function sendMessage() {
    var input = document.getElementById('chatInput');
    var message = input.value.trim();
    if (!message) return;
    sendChatMessage(message);
    input.value = '';
}

function sendChatMessage(message) {
    var messagesContainer = document.getElementById('chatMessages');
    var input = document.getElementById('chatInput');
    var sendBtn = document.getElementById('sendBtn');

    addMessage(message, 'user');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    if (sendBtn) sendBtn.disabled = true;
    if (input) input.disabled = true;

    var loadingId = addLoadingMessage();

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        removeLoadingMessage(loadingId);
        addMessage(data.response, 'bot');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    })
    .catch(function() {
        removeLoadingMessage(loadingId);
        addMessage('Sorry, something went wrong. Please try again.', 'bot');
    })
    .finally(function() {
        if (sendBtn) sendBtn.disabled = false;
        if (input) { input.disabled = false; input.focus(); }
    });
}

function addMessage(text, sender) {
    var container = document.getElementById('chatMessages');
    var div = document.createElement('div');
    div.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');

    var avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

    var content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = formatMessage(text);

    div.appendChild(avatar);
    div.appendChild(content);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatMessage(text) {
    var html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.+?)`/g, '<code style="background:rgba(124,58,237,0.15);padding:2px 6px;border-radius:4px;font-size:0.85em">$1</code>');

    var lines = html.split('\n');
    var result = '';
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line === '') {
            result += '<br>';
        } else if (line.match(/^[\d]+\.\s/)) {
            result += '<p style="margin:2px 0">' + line + '</p>';
        } else if (line.match(/^[\s]*[•\-]\s/)) {
            result += '<p style="margin:2px 0;padding-left:12px">' + line + '</p>';
        } else if (line.match(/^[\s]{2,}/)) {
            result += '<p style="margin:2px 0;padding-left:16px;color:var(--text-secondary);font-size:0.88em">' + line.trim() + '</p>';
        } else {
            result += '<p style="margin:4px 0">' + line + '</p>';
        }
    }
    return result;
}

var loadingCounter = 0;

function addLoadingMessage() {
    var id = 'loading-' + (++loadingCounter);
    var container = document.getElementById('chatMessages');
    var div = document.createElement('div');
    div.className = 'message bot-message';
    div.id = id;
    div.innerHTML = '<div class="message-avatar"><i class="fas fa-robot"></i></div><div class="message-content"><div class="spinner"></div> Thinking...</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeLoadingMessage(id) {
    var el = document.getElementById(id);
    if (el) el.remove();
}

function generatePlan() {
    var btn = event && event.target ? event.target.closest('button') : document.querySelector('[onclick="generatePlan()"]');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Generating...';
    }

    fetch('/api/plan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weeks: 4 })
    })
    .then(function(r) { return r.json(); })
    .then(function() {
        location.reload();
    })
    .catch(function() {
        alert('Failed to generate plan. Please try again.');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-calendar-plus"></i> Generate Plan';
        }
    });
}

function logSession(e) {
    e.preventDefault();
    var subject = document.getElementById('logSubject').value;
    var topic = document.getElementById('logTopic').value.trim();
    var minutes = document.getElementById('logMinutes').value;
    var resultDiv = document.getElementById('logResult');
    var btn = e.target.querySelector('button[type="submit"]');

    if (!subject || !topic) {
        showLogResult('Please select a subject and enter a topic.', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> Logging...';

    fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: subject, topic: topic, minutes: parseInt(minutes) || 30 })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) {
            showLogResult(data.message, 'success');
            document.getElementById('logTopic').value = '';
            document.getElementById('logMinutes').value = '60';
            updateDashboard();
        } else {
            showLogResult(data.message || 'Failed to log session.', 'error');
        }
    })
    .catch(function() {
        showLogResult('Network error. Please try again.', 'error');
    })
    .finally(function() {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Log Session';
    });
}

function showLogResult(message, type) {
    var div = document.getElementById('logResult');
    div.textContent = message;
    div.className = 'log-result ' + type;
    div.classList.remove('hidden');
    setTimeout(function() { div.classList.add('hidden'); }, 4000);
}

function updateDashboard() {
    fetch('/api/analyze')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (window.updateStats) window.updateStats(data);
    })
    .catch(function() {});
}
