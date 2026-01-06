/**
 * Format an entity type name for display.
 *
 * Maps internal type names to user-friendly display names.
 */
export function formatTypeName(type: string): string {
  // Special case mappings for proper display names
  const displayNames: Record<string, string> = {
    asn: 'ASN',
    cve: 'CVE',
    file_path: 'Filepath',
    hash_md5: 'MD5',
    hash_sha1: 'SHA1',
    hash_sha256: 'SHA256',
    ipv4: 'IPv4',
    ipv6: 'IPv6',
    mitre_attack: 'ATT&CK',
    url: 'URL',
    user_agent: 'User-Agent',
  }

  if (type in displayNames) {
    return displayNames[type]
  }

  // Default: replace underscores with spaces and title case
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
