document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// New Event Listeners
document.getElementById('run-sql-btn').addEventListener('click', executeSQL);
document.getElementById('cancel-sql-btn').addEventListener('click', hideReviewArea);
document.getElementById('copy-sql-btn').addEventListener('click', copySQL);

// On startup
document.addEventListener('DOMContentLoaded', loadModels);

function loadModels() {
    fetch('/models')
        .then(response => response.json())
        .then(models => {
            const select = document.getElementById('model-select');
            select.innerHTML = '';

            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;

                // Set default
                if (model.id === 'models/gemma-3-27b-it') {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        })
        .catch(err => {
            console.error("Failed to load models", err);
            const select = document.getElementById('model-select');
            select.innerHTML = '<option disabled>Error loading models</option>';
        });
}

function sendMessage() {
    const input = document.getElementById('user-input');
    const modelSelect = document.getElementById('model-select');
    const message = input.value.trim();
    const model = modelSelect.value;

    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    // Hide previous results
    hideReviewArea();
    hideResultArea();

    // Show loading...
    const loadingId = addMessage('Thinking...', 'assistant');

    fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, model: model })
    })
        .then(response => response.json())
        .then(data => {
            removeMessage(loadingId);
            if (data.error) {
                addMessage('Error: ' + data.error, 'system');
            } else {
                showReviewArea(data.sql);
                addMessage("I've generated a query. Please review it above before executing.", 'assistant');
            }
        })
        .catch(error => {
            removeMessage(loadingId);
            addMessage('Error: ' + error, 'system');
        });
}

function showReviewArea(sql) {
    const area = document.getElementById('sql-review-area');
    const editor = document.getElementById('sql-editor');
    editor.value = sql;
    area.style.display = 'block';
    area.scrollIntoView({ behavior: 'smooth' });
}

function hideReviewArea() {
    document.getElementById('sql-review-area').style.display = 'none';
}

function hideResultArea() {
    document.getElementById('result-area').style.display = 'none';
}

function copySQL() {
    const sql = document.getElementById('sql-editor').value;
    navigator.clipboard.writeText(sql).then(() => {
        const btn = document.getElementById('copy-sql-btn');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = originalText, 2000);
    });
}

function executeSQL() {
    const sql = document.getElementById('sql-editor').value;
    if (!sql) return;

    // Show loading indicator in result area or chat?
    // Let's use chat to show progress
    const loadingId = addMessage('Executing query...', 'assistant');

    fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: sql })
    })
        .then(response => response.json())
        .then(data => {
            removeMessage(loadingId);
            if (data.error) {
                addMessage('Execution Error: ' + data.error, 'system');
            } else {
                showResultArea(data);
                addMessage(`Query executed successfully. ${data.rows} rows returned.`, 'assistant');
            }
        })
        .catch(error => {
            removeMessage(loadingId);
            addMessage('Network Error: ' + error, 'system');
        });
}

function showResultArea(data) {
    const area = document.getElementById('result-area');
    const preview = document.getElementById('result-preview');
    const downloadLink = document.getElementById('download-link');

    if (data.preview) {
        preview.innerHTML = buildTable(data.preview);
    }

    if (data.rows && data.rows > 0) {
        downloadLink.href = "#";
        downloadLink.style.display = 'inline-block';
        downloadLink.textContent = `Download CSV (${data.rows} rows)`;

        // Remove old listeners to avoid duplicates if any (though usually clean slate)
        const newBtn = downloadLink.cloneNode(true);
        downloadLink.parentNode.replaceChild(newBtn, downloadLink);

        newBtn.addEventListener('click', (e) => {
            e.preventDefault();
            downloadCSV();
        });
    } else {
        downloadLink.style.display = 'none';
    }

    area.style.display = 'block';
    area.scrollIntoView({ behavior: 'smooth' });
}

function addMessage(text, type) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.id = 'msg-' + Date.now();

    if (type !== 'user') {
        msgDiv.innerHTML = text;
    } else {
        msgDiv.textContent = text;
    }

    chatBox.appendChild(msgDiv);
    // Scroll window to bottom smoothly
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
    return msgDiv.id;
}

function removeMessage(id) {
    const msg = document.getElementById(id);
    if (msg) msg.remove();
}

function buildTable(data) {
    if (data.length === 0) return '<p>No data returned.</p>';
    const headers = Object.keys(data[0]);
    let html = '<table><thead><tr>';

    headers.forEach(h => html += `<th>${h}</th>`);
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        headers.forEach(h => html += `<td>${row[h]}</td>`);
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function downloadCSV() {
    const sql = document.getElementById('sql-editor').value;
    if (!sql) return;

    // Use a more specific selector if possible, or ID
    // In showResultArea we act on an element with specific ID or class
    // The previously modified code uses document.getElementById('download-link')
    // but here we select by class. Let's standarize on ID if possible, but class is fine if unique.
    const btn = document.getElementById('download-link'); // Safer
    const originalText = btn.textContent;
    btn.textContent = 'Preparing Download...';
    // rudimentary disabled state
    btn.style.pointerEvents = 'none';
    btn.style.opacity = '0.7';

    fetch('/download_csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: sql })
    })
        .then(response => {
            if (!response.ok) throw new Error("Download failed");
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'results.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            btn.textContent = originalText;
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        })
        .catch(error => {
            console.error('Download error:', error);
            btn.textContent = 'Error Downloading';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.pointerEvents = 'auto';
                btn.style.opacity = '1';
            }, 3000);
        });
}
