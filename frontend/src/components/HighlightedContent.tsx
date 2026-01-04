import { useMemo } from 'react'
import type { Extracted } from '../types'
import { getEntityHighlightColor } from '../utils/entityColors'
import { useTheme } from '../hooks/useTheme'

interface HighlightedContentProps {
  content: string
  extracted: Extracted[]
  className?: string
}

interface HighlightSegment {
  text: string
  entityIndex: number | null // null means no highlight
  start: number
  end: number
}

export default function HighlightedContent({
  content,
  extracted,
  className = '',
}: HighlightedContentProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  // Build segments with highlights
  const segments = useMemo(() => {
    if (extracted.length === 0) {
      return [{ text: content, entityIndex: null, start: 0, end: content.length }]
    }

    // Find all matches for each entity in the content
    const matches: Array<{ start: number; end: number; entityIndex: number }> = []

    extracted.forEach((entity, entityIndex) => {
      // Search for the value (or raw_value if different)
      const searchTerms = [entity.value]
      if (entity.raw_value && entity.raw_value !== entity.value) {
        searchTerms.push(entity.raw_value)
      }

      for (const term of searchTerms) {
        let pos = 0
        while (pos < content.length) {
          const idx = content.toLowerCase().indexOf(term.toLowerCase(), pos)
          if (idx === -1) break

          matches.push({
            start: idx,
            end: idx + term.length,
            entityIndex,
          })
          pos = idx + 1
        }
      }
    })

    if (matches.length === 0) {
      return [{ text: content, entityIndex: null, start: 0, end: content.length }]
    }

    // Sort by start position
    matches.sort((a, b) => a.start - b.start)

    // Remove overlapping matches (keep earlier/longer ones)
    const filteredMatches: typeof matches = []
    for (const match of matches) {
      const overlaps = filteredMatches.some(
        m => (match.start >= m.start && match.start < m.end) ||
             (match.end > m.start && match.end <= m.end)
      )
      if (!overlaps) {
        filteredMatches.push(match)
      }
    }

    // Build segments
    const result: HighlightSegment[] = []
    let lastEnd = 0

    for (const match of filteredMatches) {
      // Add non-highlighted segment before this match
      if (match.start > lastEnd) {
        result.push({
          text: content.slice(lastEnd, match.start),
          entityIndex: null,
          start: lastEnd,
          end: match.start,
        })
      }

      // Add highlighted segment
      result.push({
        text: content.slice(match.start, match.end),
        entityIndex: match.entityIndex,
        start: match.start,
        end: match.end,
      })

      lastEnd = match.end
    }

    // Add remaining non-highlighted segment
    if (lastEnd < content.length) {
      result.push({
        text: content.slice(lastEnd),
        entityIndex: null,
        start: lastEnd,
        end: content.length,
      })
    }

    return result
  }, [content, extracted])

  return (
    <span className={className}>
      {segments.map((segment, idx) => {
        if (segment.entityIndex === null) {
          return <span key={idx}>{segment.text}</span>
        }

        const bgColor = getEntityHighlightColor(segment.entityIndex, isDark)
        return (
          <mark
            key={idx}
            style={{
              backgroundColor: bgColor,
              color: 'inherit',
              borderRadius: '2px',
              padding: '1px 2px',
              margin: '-1px -2px',
            }}
            title={`Entity: ${extracted[segment.entityIndex]?.value}`}
          >
            {segment.text}
          </mark>
        )
      })}
    </span>
  )
}
