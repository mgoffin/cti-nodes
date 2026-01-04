/**
 * Utility for generating consistent highlight colors for extracted entities.
 * Each entity gets a unique soft color based on its index.
 */

// Soft pastel colors that work well for highlighting in both light and dark modes
// Each color has light and dark mode variants
const HIGHLIGHT_PALETTE = [
  { light: 'rgba(251, 191, 36, 0.3)', dark: 'rgba(251, 191, 36, 0.25)' },   // amber
  { light: 'rgba(52, 211, 153, 0.3)', dark: 'rgba(52, 211, 153, 0.25)' },   // emerald
  { light: 'rgba(96, 165, 250, 0.3)', dark: 'rgba(96, 165, 250, 0.25)' },   // blue
  { light: 'rgba(251, 146, 60, 0.3)', dark: 'rgba(251, 146, 60, 0.25)' },   // orange
  { light: 'rgba(167, 139, 250, 0.3)', dark: 'rgba(167, 139, 250, 0.25)' }, // violet
  { light: 'rgba(248, 113, 113, 0.3)', dark: 'rgba(248, 113, 113, 0.25)' }, // red
  { light: 'rgba(45, 212, 191, 0.3)', dark: 'rgba(45, 212, 191, 0.25)' },   // teal
  { light: 'rgba(244, 114, 182, 0.3)', dark: 'rgba(244, 114, 182, 0.25)' }, // pink
  { light: 'rgba(163, 230, 53, 0.3)', dark: 'rgba(163, 230, 53, 0.25)' },   // lime
  { light: 'rgba(129, 140, 248, 0.3)', dark: 'rgba(129, 140, 248, 0.25)' }, // indigo
]

// Border colors for entity badges (slightly more saturated)
const BORDER_PALETTE = [
  { light: 'rgb(251, 191, 36)', dark: 'rgb(251, 191, 36)' },   // amber
  { light: 'rgb(52, 211, 153)', dark: 'rgb(52, 211, 153)' },   // emerald
  { light: 'rgb(96, 165, 250)', dark: 'rgb(96, 165, 250)' },   // blue
  { light: 'rgb(251, 146, 60)', dark: 'rgb(251, 146, 60)' },   // orange
  { light: 'rgb(167, 139, 250)', dark: 'rgb(167, 139, 250)' }, // violet
  { light: 'rgb(248, 113, 113)', dark: 'rgb(248, 113, 113)' }, // red
  { light: 'rgb(45, 212, 191)', dark: 'rgb(45, 212, 191)' },   // teal
  { light: 'rgb(244, 114, 182)', dark: 'rgb(244, 114, 182)' }, // pink
  { light: 'rgb(163, 230, 53)', dark: 'rgb(163, 230, 53)' },   // lime
  { light: 'rgb(129, 140, 248)', dark: 'rgb(129, 140, 248)' }, // indigo
]

export function getEntityHighlightColor(index: number, isDark: boolean): string {
  const colorIndex = index % HIGHLIGHT_PALETTE.length
  return isDark ? HIGHLIGHT_PALETTE[colorIndex].dark : HIGHLIGHT_PALETTE[colorIndex].light
}

export function getEntityBorderColor(index: number, isDark: boolean): string {
  const colorIndex = index % BORDER_PALETTE.length
  return isDark ? BORDER_PALETTE[colorIndex].dark : BORDER_PALETTE[colorIndex].light
}

export function getColorPaletteLength(): number {
  return HIGHLIGHT_PALETTE.length
}
