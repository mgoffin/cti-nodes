// Prevent multiple instances of the listener
if (!window.nodesExtensionLoaded) {
  window.nodesExtensionLoaded = true;

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'showToast') {
      showToast(message);
    }
  });
}

// Show toast notification
function showToast(data) {
  // Create toast container if it doesn't exist
  let container = document.getElementById('nodes-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'nodes-toast-container';
    container.className = 'nodes-toast-container';
    document.body.appendChild(container);
  }

  // Clear all existing toasts
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `nodes-toast ${data.success ? 'nodes-toast-success' : 'nodes-toast-error'}`;

  // Create message content
  const messageDiv = document.createElement('div');
  messageDiv.className = 'nodes-toast-message';
  messageDiv.textContent = data.message;
  toast.appendChild(messageDiv);

  // Add link to node if successful
  if (data.success && data.nodeId) {
    const link = document.createElement('a');
    link.href = `${data.frontendUrl}/node/${data.nodeId}`;
    link.target = '_blank';
    link.className = 'nodes-toast-link';
    link.textContent = 'Open Node →';
    toast.appendChild(link);
  }

  // Add close button
  const closeBtn = document.createElement('button');
  closeBtn.className = 'nodes-toast-close';
  closeBtn.innerHTML = '×';
  closeBtn.onclick = () => removeToast(toast);
  toast.appendChild(closeBtn);

  // Add to container
  container.appendChild(toast);

  // Auto-remove after 5 seconds
  setTimeout(() => removeToast(toast), 5000);

  // Trigger animation
  setTimeout(() => toast.classList.add('nodes-toast-show'), 10);
}

// Remove toast with animation
function removeToast(toast) {
  toast.classList.remove('nodes-toast-show');
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}
