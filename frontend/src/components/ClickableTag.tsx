import { useNavigate } from 'react-router'
import type { Tag } from '../types'

interface ClickableTagProps {
  tag: Tag
  variant?: 'source' | 'custom' | 'default'
  showName?: boolean
  truncateAt?: number
  onClick?: (e: React.MouseEvent) => void
}

export default function ClickableTag({
  tag,
  variant = 'custom',
  showName = true,
  truncateAt = 30,
  onClick,
}: ClickableTagProps) {
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onClick) {
      onClick(e)
    } else {
      // Navigate to search with tag query
      const query = `tag:${tag.name}="${tag.value}"`
      navigate(`/?q=${encodeURIComponent(query)}`)
    }
  }

  const displayValue = truncateAt && tag.value.length > truncateAt
    ? `${tag.value.substring(0, truncateAt)}...`
    : tag.value

  const tagClass = `tag tag-${variant} tag-clickable`

  return (
    <button
      type="button"
      onClick={handleClick}
      className={tagClass}
      title={`Search for ${tag.name}: ${tag.value}`}
    >
      {showName ? `${tag.name}: ${displayValue}` : displayValue}
    </button>
  )
}
