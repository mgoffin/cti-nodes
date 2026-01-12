// Load saved settings
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.sync.get(['apiUrl', 'frontendUrl'], (result) => {
    document.getElementById('apiUrl').value = result.apiUrl || 'http://localhost:8000';
    document.getElementById('frontendUrl').value = result.frontendUrl || 'http://localhost:5173';
  });
});

// Save settings
document.getElementById('save').addEventListener('click', () => {
  const apiUrl = document.getElementById('apiUrl').value.trim();
  const frontendUrl = document.getElementById('frontendUrl').value.trim();

  // Validate URLs
  if (!apiUrl || !frontendUrl) {
    showStatus('Please enter both URLs', false);
    return;
  }

  try {
    new URL(apiUrl);
    new URL(frontendUrl);
  } catch (e) {
    showStatus('Please enter valid URLs', false);
    return;
  }

  // Save to storage
  chrome.storage.sync.set({
    apiUrl: apiUrl,
    frontendUrl: frontendUrl
  }, () => {
    showStatus('Settings saved successfully!', true);
  });
});

function showStatus(message, success) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${success ? 'success' : 'error'}`;

  setTimeout(() => {
    status.className = 'status';
  }, 3000);
}
