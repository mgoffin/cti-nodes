import { Link } from 'react-router'
import { format } from 'date-fns'
import type { Node } from '../types'
import ClickableTag from './ClickableTag'
import ClickableSource from './ClickableSource'

interface NodeListProps {
  nodes: Node[]
}

export default function NodeList({ nodes }: NodeListProps) {
  return (
    <div className="space-y-4">
      {nodes.map((node) => (
        <NodeCard key={node.id} node={node} />
      ))}
    </div>
  )
}

function NodeCard({ node }: { node: Node }) {
  const sourceTag = node.tags.find(t => t.name === 'source')
  const datetimeTag = node.tags.find(t => t.name === 'datetime')
  const customTags = node.tags.filter(t => t.name !== 'source' && t.name !== 'datetime')

  // Truncate content for preview
  const preview = node.content.length > 300
    ? node.content.substring(0, 300) + '...'
    : node.content

  return (
    <Link to={`/node/${node.id}`} className="block">
      <div className="card hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Content preview */}
            <p className="theme-text-primary whitespace-pre-wrap break-words">
              {preview}
            </p>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mt-3">
              {sourceTag && (
                <ClickableSource source={sourceTag.value} truncateAt={40} />
              )}
              {customTags.map((tag) => (
                <ClickableTag key={tag.id} tag={tag} variant="custom" />
              ))}
            </div>
          </div>

          {/* Timestamp */}
          <div className="ml-4 text-right flex-shrink-0">
            <p className="text-xs theme-text-subtle">
              {datetimeTag
                ? format(new Date(datetimeTag.value), 'MMM d, yyyy')
                : format(new Date(node.created_at), 'MMM d, yyyy')}
            </p>
            <p className="text-xs theme-text-subtle">
              {datetimeTag
                ? format(new Date(datetimeTag.value), 'h:mm a')
                : format(new Date(node.created_at), 'h:mm a')}
            </p>
          </div>
        </div>
      </div>
    </Link>
  )
}
