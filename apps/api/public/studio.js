const form = document.getElementById('renderForm');
const input = document.getElementById('promptInput');
const resultArea = document.getElementById('resultArea');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = input.value.trim();
    if (!prompt) return;

    resultArea.innerHTML = "<p>Manifesting parchment...</p>";

    const response = await fetch('/api/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
    });

    const data = await response.json();
    resultArea.innerHTML = `<img src="${data.imageUrl}" alt="Rendered parchment" />`;
});
