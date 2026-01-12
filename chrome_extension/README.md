# Nodes Chrome Extension

A Chrome extension that allows you to quickly add content to Nodes and search directly from any webpage.

## Features

### 1. Add to Nodes
- Right-click on any selected text
- Choose "Add to Nodes"
- Creates a new node with:
  - **Content**: Your selected text
  - **Source**: The current page URL
- Shows a success toast with a direct link to the new node

### 2. Search Value in Nodes
- Right-click on any selected text
- Choose "Search Value in Nodes"
- Opens a new tab with a search for that value in your Nodes instance

### 3. Search Source in Nodes
- Right-click anywhere on a page
- Choose "Search Source in Nodes"
- Opens a new tab searching for nodes that have the current page URL as their source

## Installation

1. **Enable Developer Mode** in Chrome:
   - Open Chrome and navigate to `chrome://extensions/`
   - Toggle "Developer mode" in the top-right corner

2. **Load the Extension**:
   - Click "Load unpacked"
   - Navigate to the `chrome_extension` folder in your Nodes project
   - Select the folder

3. **Configure Settings**:
   - Click the extension icon in your toolbar
   - Enter your API URL (default: `http://localhost:8000`)
   - Enter your Frontend URL (default: `http://localhost:5173`)
   - Click "Save Settings"

## Usage

1. **Adding Content**:
   - Browse any webpage
   - Highlight the text you want to add to Nodes
   - Right-click and select "Add to Nodes"
   - A toast notification will appear with a link to your new node

2. **Searching**:
   - Highlight any text and right-click to search for that value
   - Or right-click anywhere to search for nodes from the current page source

## Configuration

The extension stores your API and Frontend URLs in Chrome's sync storage. You can change these at any time by clicking the extension icon and updating the settings.

### Default URLs
- **API URL**: `http://localhost:8000`
- **Frontend URL**: `http://localhost:5173`

For production deployments, update these to your actual server URLs.

## Permissions

The extension requires the following permissions:
- **contextMenus**: To add right-click menu options
- **activeTab**: To access the current page URL and selected text
- **storage**: To save your configuration settings

## Troubleshooting

**Extension not working?**
- Make sure your Nodes backend is running
- Check that the API and Frontend URLs in settings are correct
- Verify that Developer Mode is enabled in Chrome
- Check the browser console for any error messages
- After installing or updating the extension, reload the webpage you're testing on

**Toast notifications not showing?**
- Refresh the webpage after installing the extension
- Check that content scripts are allowed to run on the site
- If the extension was just installed, try reloading the page
- Check the browser console (F12) for any errors

**Context menu items not appearing?**
- Try reloading the extension in `chrome://extensions/`
- Make sure you've selected text before right-clicking (for "Add to Nodes" and "Search Value")
- Right-click directly on the selected text

**Newlines not preserved in content?**
- Chrome's `selectionText` API may collapse some whitespace when copying from webpages
- This is a browser limitation - the extension sends exactly what Chrome provides
- For best results, copy from sources that maintain formatting (like code blocks or pre-formatted text)
