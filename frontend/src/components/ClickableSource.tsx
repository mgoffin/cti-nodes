import { useNavigate } from 'react-router'

interface ClickableSourceProps {
  source: string
  truncateAt?: number
  onClick?: (e: React.MouseEvent) => void
}

export default function ClickableSource({
  source,
  truncateAt = 30,
  onClick,
}: ClickableSourceProps) {
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onClick) {
      onClick(e)
    } else {
      // Navigate to search for nodes with same source
      const query = `tag:source="${source}"`
      navigate(`/?q=${encodeURIComponent(query)}`)
    }
  }

  const displayValue = truncateAt && source.length > truncateAt
    ? `${source.substring(0, truncateAt)}...`
    : source

  return (
    <button
      type="button"
      onClick={handleClick}
      className="tag tag-source tag-clickable"
      title={`Search for source: ${source}`}
    >
      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
        />
      </svg>
      {displayValue}
    </button>
  )
}
