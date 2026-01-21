# User Guide

Complete guide to using the Nodes platform.

## Your First Node

1. Click **New Node** button
2. Add your content - paste or type intelligence snippets
3. Add a **source** tag (required) - URL, person, document name, etc.
4. Add custom tags (optional) - type to see suggestions from existing tags
5. Click **Save**

The system automatically:
- Extracts IOCs (IPs, domains, hashes, URLs, emails)
- Extracts entities (threat actors, malware, tools)
- Finds and links related nodes
- Shows connection notifications

## Understanding the Interface

### List View (Default)

Shows nodes in a list with:
- **Content preview** - Click to expand full content
- **Tags** - Click to search for that tag value
- **Extracted entities** - Highlighted and clickable
- **Related Nodes** - Shows connected nodes inline
- **Comments** - Markdown-formatted discussions

### Graph View

Visual network representation:
- **Nodes** - Colored by type or tag
- **Edges** - Lines between related nodes
- **Depth slider** - Control how many connection levels to show
- **Click nodes** - Focus and explore connections
- **Drag** - Rearrange graph layout

Toggle between views using the **List/Graph** button.

## Tags

### System Tags (Automatic)

- **datetime** - Auto-generated timestamp
- **source** - Required on creation (where you got the intel)

### Suggested Tags

When creating nodes, Nodes suggests tags based on extracted content:
- **iocs** - When IOCs are detected
- **malware** - When malware families are found
- **attribution** - When threat actors are mentioned
- **vulnerability** - When CVEs are detected

You can accept or reject these suggestions.

### Custom Tags

Add your own tags to organize nodes:
- Type tag name, then value
- Suggestions appear from existing tags
- Common tags: `campaign`, `severity`, `tactic`, `technique`

**Clicking tags** in the interface searches for that tag value across all nodes.

## Extracted Entities

Nodes automatically detects and extracts:

| Type | Examples |
|------|----------|
| **IPv4/IPv6** | `192.168.1.1`, `2001:db8::1` |
| **Domains** | `evil.com`, `malicious.example.org` |
| **URLs** | `https://badsite.com/payload.exe` |
| **Hashes** | MD5, SHA1, SHA256 |
| **Emails** | `attacker@evil.com` |
| **CVEs** | `CVE-2024-1234` |
| **Threat Actors** | APT28, Fancy Bear (normalized to Microsoft naming) |
| **Malware** | Cobalt Strike, Mimikatz, TrickBot |
| **Tools** | Various attacker tools |
| **Commands** | Command-line strings |
| **File Paths** | Windows and Unix paths |
| **Registry Keys** | Windows registry keys |

### Entity Actions

- **Click** - Search for that entity across all nodes
- **Hover** - See if it appears in other nodes
- **Raw value** - See original format before normalization

### Entity Validation

The system detects and suggests corrections for:
- **Type mismatches** - e.g., filename labeled as domain
- **Defanged IOCs** - e.g., `192[.]168[.]1[.]1` → suggests refanging

Accept or reject validation suggestions as needed.

### Suggested Entities

Nodes analyzes related nodes and suggests entities you might want to add:
- **Auto-detected** - Finds entities from connected nodes in your content
- **One-click accept** - Add suggested entity instantly
- **Reject** - Hide suggestion permanently
- **Bulk operations** - Accept/reject all at once

## Search

### Basic Search

Just type in the search bar:
- Searches everywhere (content + all tags)
- Use `*` for wildcards: `*cobalt*`

### Advanced Search Syntax

| Query | What it searches |
|-------|------------------|
| `keyword` | Everywhere (content + tags) |
| `content="*text*"` | Node content only |
| `tag:source="*twitter*"` | Specific tag by name and value |
| `tag:adversary=*` | All nodes with a specific tag name |
| `tag-value="*apt28*"` | All tag values (any tag name) |

### Combining Searches

Use `AND` / `OR` to combine:
```
content="*ransomware*" AND tag:source="*twitter*"
content="*cobalt strike*" OR content="*mimikatz*"
tag:malware=* AND tag:severity="high"
```

### Search Tips

- Use wildcards `*` liberally: `*partial*match*`
- Quote values with spaces: `"multiple words"`
- Tag names are case-insensitive
- Search is fast thanks to FTS5 indexing

## Auto-Linking

Nodes automatically creates edges (connections) between related nodes based on:

### IOC Matches (High Confidence)
Same IP, domain, hash, email, or URL across nodes.

### Entity Matches (High Confidence)
Same threat actor, malware family, or tool.

### Tag Matches (Medium Confidence)
Exact tag name and value match.

### Content Overlap (Low Confidence)
Significant shared keywords.

### Edge Confidence Scoring

| Match Type | Confidence | Meaning |
|------------|------------|---------|
| Exact IOC | 1.0 | Same indicator |
| Threat actor (canonical) | 1.0 | Normalized name match |
| Threat actor (alias) | 0.9 | Matched via alias |
| Tag match | 0.8 | Same tag name+value |
| URL domain | 0.7 | Same domain, different paths |
| Content overlap | 0.3-0.6 | Shared keywords |
| Manual | 1.0 | User-created edge |

Higher confidence = stronger relationship.

## Comments

Add markdown-formatted comments to nodes:
- **Collaborate** - Discuss findings with team members
- **Document** - Add analysis notes
- **Markdown** - Use headers, lists, code blocks, etc.

When authentication is enabled, comments show author and timestamp.

## Threat Actor Normalization

Nodes uses Microsoft's threat actor naming convention as the canonical standard:

| Common Names | Microsoft Name |
|--------------|----------------|
| APT28, Fancy Bear, Sofacy | Forest Blizzard |
| APT29, Cozy Bear | Midnight Blizzard |
| Lazarus Group | Diamond Sleet |

When you enter "APT28", Nodes:
1. Recognizes it as an alias
2. Links to nodes mentioning "Forest Blizzard"
3. Shows canonical name in the UI

This ensures all references connect even with different naming.

## Dark/Light Theme

Toggle between dark and light modes:
- Click the theme toggle in the header
- Preference is saved automatically
- Works in both List and Graph views

## Chrome Extension

Capture intelligence while browsing the web.

### Installation

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome_extension` folder
5. Configure API and frontend URLs in extension popup

### Features

- **Add to Nodes** - Right-click selected text to create node
- **Search Value** - Search for highlighted text
- **Search Source** - Find nodes from current page URL
- **Toast Notifications** - Instant feedback with links

See [chrome-extension.md](chrome-extension.md) for details.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `N` | New Node |
| `/` | Focus search |
| `Esc` | Clear search |
| `L` | Toggle List/Graph view |

## Tips & Best Practices

### Organizing Nodes

- **Be consistent with sources** - Use same format for URLs, Twitter handles, etc.
- **Tag liberally** - More tags = better connections
- **Use campaigns** - Track related activity with campaign tags
- **Severity tags** - Prioritize with high/medium/low

### Effective Searching

- Start broad, narrow down with AND
- Use wildcards for partial matches
- Search by source to review specific intel streams
- Search by tag to find themed collections

### Leveraging Auto-Linking

- **Check related nodes** - Often reveals connections you missed
- **Follow the graph** - Explore multi-hop connections
- **High confidence edges** - Focus on IOC/entity matches first
- **Review notifications** - New connections appear as you add nodes

### Managing Large Databases

- **Use tags extensively** - Essential for filtering
- **Archive old campaigns** - Tag as `archived` or similar
- **Search before creating** - Avoid duplicate nodes
- **Prune dead links** - Remove nodes that are no longer relevant

## Multi-User Features (When Auth Enabled)

### Roles

- **Administrator** - Manage users, full access, audit logs
- **Analyst** - Create/edit own content, view all
- **Viewer** - Read-only access

### User Profile

- Customize display name
- Upload avatar
- Set theme preference
- View your content stats

### Session Management

- View active sessions
- Revoke sessions from other devices
- See last login time and IP

### Audit Logs (Admin Only)

- Track all modifications
- See who changed what and when
- Filter by user, action, date
- Configurable retention

## Next Steps

- **Chrome extension**: [chrome-extension.md](chrome-extension.md)
- **Advanced search**: Practice with query syntax
- **Production deployment**: [production-deployment.md](production-deployment.md)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
