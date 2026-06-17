function loadPage(page) {
    fetch(page)
        .then(response => response.text())
        .then(html => {
            document.getElementById('content').innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading page:', error);
        });
}

function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value;
    chatInput.value = '';
    const div = document.createElement('div');
    div.textContent = 'You: ' + message;
    chatMessages.appendChild(div);
}
