# Chrome Extension

The Nodes Chrome Extension allows you to capture intelligence directly from any webpage while browsing.

## Features

- **Add to Nodes** - Right-click selected text to create a new node with the page URL as source
- **Search Value** - Quickly search for highlighted text in your Nodes database
- **Search Source** - Find all nodes that reference the current page URL
- **Toast Notifications** - Get instant feedback with links to newly created nodes

## Installation

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select the `chrome_extension` folder from your Nodes installation
5. Click the extension icon to configure URLs:
   - **API URL**: `http://localhost:8000` (or your server URL)
   - **Frontend URL**: `http://localhost:5173` (or your server URL)
6. Click "Save Settings"

## Usage

### Adding Content

1. Browse any webpage
2. Highlight text you want to capture
3. Right-click → "Add to Nodes"
4. Toast notification appears with link to new node

### Searching

- **Search for highlighted text**: Highlight → Right-click → "Search Value in Nodes"
- **Search for current page**: Right-click anywhere → "Search Source in Nodes"

## Configuration

### Production Deployment

Update URLs in extension popup:
```
API URL: https://threat-intel.company.com
Frontend URL: https://threat-intel.company.com
```

### CORS Configuration

If extension shows "Failed to connect", add to your `.env`:

```bash
NODES_CORS_ORIGINS=["http://localhost:8000","chrome-extension://your-extension-id"]
```

To find your extension ID:
1. Go to `chrome://extensions/`
2. Find Nodes extension
3. Copy the ID shown below the extension name

## Permissions

The extension requires:
- **contextMenus** - Right-click menu options
- **activeTab** - Access current page URL and selected text
- **storage** - Save configuration settings

## Troubleshooting

### Extension Not Working

**Check backend is running:**
```bash
curl http://localhost:8000/api/health
```

**Verify URLs in settings:**
- Click extension icon
- Check API and Frontend URLs are correct
- Click "Save Settings"

**Reload webpage:**
- After installing extension, reload the page you're testing on

### Toast Notifications Not Showing

- Refresh webpage after installing extension
- Check browser allows notifications
- Check browser console (F12) for errors

### Context Menu Not Appearing

- Reload extension in `chrome://extensions/`
- Ensure text is selected before right-clicking (for "Add to Nodes")
- Try reloading the webpage

### "Failed to Connect" Error

1. Verify Nodes is running
2. Check API URL in extension settings
3. Ensure CORS is configured (see above)
4. Check browser console for specific error

### Newlines Not Preserved

Chrome's `selectionText` API may collapse whitespace. This is a browser limitation. For best results, copy from:
- Code blocks
- Pre-formatted text
- Plain text sources

## Firefox Support

Currently Chrome/Edge only. Firefox support may be added in future.

## Development

Extension files location: `chrome_extension/`

Key files:
- `manifest.json` - Extension configuration
- `background.js` - Service worker (context menu handling)
- `content.js` - Content script (toast notifications)
- `popup.html/js` - Settings popup
- `toast.css` - Toast notification styling

## Next Steps

- **User guide**: [user-guide.md](user-guide.md)
- **Configuration**: [configuration.md](configuration.md)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)

## Original README

See [chrome_extension/README.md](../chrome_extension/README.md) for the complete original documentation.
