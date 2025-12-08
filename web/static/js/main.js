document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    
    // Show loading...
    const loadingId = addMessage('Thinking...', 'assistant');

    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeMessage(loadingId);
        displayResult(data);
    })
    .catch(error => {
        removeMessage(loadingId);
        addMessage('Error: ' + error, 'system');
    });
}

function addMessage(text, type) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.id = 'msg-' + Date.now();
    
    // Allow HTML for system/assistant messages
    if (type !== 'user') {
        msgDiv.innerHTML = text;
    } else {
        msgDiv.textContent = text;
    }
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msgDiv.id;
}

function removeMessage(id) {
    const msg = document.getElementById(id);
    if (msg) msg.remove();
}

function displayResult(data) {
    let content = `<p>${data.explanation}</p>`;
    
    if (data.sql) {
        content += `<div class="sql-block">${data.sql}</div>`;
    }
    
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        content += buildTable(data.data);
    } else if (data.data) {
        content += `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
    }

    addMessage(content, 'assistant');
}

function buildTable(data) {
    if (data.length === 0) return '';
    const headers = Object.keys(data[0]);
    let html = '<div class="data-preview"><table><thead><tr>';
    
    headers.forEach(h => html += `<th>${h}</th>`);
    html += '</tr></thead><tbody>';
    
    // Limit to 10 rows for display
    data.slice(0, 10).forEach(row => {
        html += '<tr>';
        headers.forEach(h => html += `<td>${row[h]}</td>`);
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    if (data.length > 10) {
        html += `<p style="font-size:0.8em">Showing 10 of ${data.length} rows.</p>`;
    }
    return html;
}
