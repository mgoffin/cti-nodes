import { useNavigate } from 'react-router'
import type { Extracted } from '../types'

interface ClickableExtractedProps {
  extracted: Extracted
  onClick?: (e: React.MouseEvent) => void
}

export default function ClickableExtracted({
  extracted,
  onClick,
}: ClickableExtractedProps) {
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onClick) {
      onClick(e)
    } else {
      // Navigate to search - use the value for freeform search
      navigate(`/?q=${encodeURIComponent(extracted.value)}`)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="extracted-clickable inline-flex items-center"
      title={`Search for "${extracted.value}"`}
    >
      <code className="text-sm theme-text-primary">{extracted.value}</code>
      {extracted.canonical_value && extracted.canonical_value !== extracted.value && (
        <span className="text-sm theme-text-muted ml-2">
          → {extracted.canonical_value}
        </span>
      )}
    </button>
  )
}
