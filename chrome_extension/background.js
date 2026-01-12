// Default API URL (can be configured in popup)
let API_URL = 'http://localhost:8000';
let FRONTEND_URL = 'http://localhost:5173';

// Load saved settings
chrome.storage.sync.get(['apiUrl', 'frontendUrl'], (result) => {
  if (result.apiUrl) API_URL = result.apiUrl;
  if (result.frontendUrl) FRONTEND_URL = result.frontendUrl;
});

// Listen for settings changes
chrome.storage.onChanged.addListener((changes) => {
  if (changes.apiUrl) API_URL = changes.apiUrl.newValue;
  if (changes.frontendUrl) FRONTEND_URL = changes.frontendUrl.newValue;
});

// Create context menu items
chrome.runtime.onInstalled.addListener(() => {
  // Create parent menu
  chrome.contextMenus.create({
    id: 'nodesParent',
    title: 'Nodes Extension',
    contexts: ['page', 'selection']
  });

  // Menu item for adding selected text to Nodes
  chrome.contextMenus.create({
    id: 'addToNodes',
    parentId: 'nodesParent',
    title: 'Add to Nodes',
    contexts: ['selection']
  });

  // Menu item for searching selected value in Nodes
  chrome.contextMenus.create({
    id: 'searchValue',
    parentId: 'nodesParent',
    title: 'Search Value in Nodes',
    contexts: ['selection']
  });

  // Menu item for searching page source in Nodes
  chrome.contextMenus.create({
    id: 'searchSource',
    parentId: 'nodesParent',
    title: 'Search Source in Nodes',
    contexts: ['page', 'selection']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'addToNodes') {
    addToNodes(info.selectionText, info.pageUrl, tab);
  } else if (info.menuItemId === 'searchValue') {
    searchValue(info.selectionText);
  } else if (info.menuItemId === 'searchSource') {
    searchSource(info.pageUrl);
  }
});

// Add selected text to Nodes
async function addToNodes(content, source, tab) {
  try {
    const response = await fetch(`${API_URL}/api/nodes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content,
        source: source
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const node = await response.json();

    // Send success message to content script
    chrome.tabs.sendMessage(tab.id, {
      type: 'showToast',
      success: true,
      message: 'Added to Nodes successfully!',
      nodeId: node.id,
      frontendUrl: FRONTEND_URL
    }).catch(err => {
      console.error('Failed to send toast message:', err);
      console.log('Note: Content script may not be loaded. Try refreshing the page.');
    });
  } catch (error) {
    console.error('Error adding to Nodes:', error);

    // Send error message to content script
    chrome.tabs.sendMessage(tab.id, {
      type: 'showToast',
      success: false,
      message: `Failed to add to Nodes: ${error.message}`
    }).catch(err => {
      console.error('Failed to send toast message:', err);
    });
  }
}

// Search for selected value in Nodes
function searchValue(value) {
  const searchUrl = `${FRONTEND_URL}/?q=${encodeURIComponent(value)}`;
  chrome.tabs.create({ url: searchUrl });
}

// Search for page source in Nodes
function searchSource(pageUrl) {
  const searchUrl = `${FRONTEND_URL}/?q=${encodeURIComponent(`source="${pageUrl}"`)}`;
  chrome.tabs.create({ url: searchUrl });
}
