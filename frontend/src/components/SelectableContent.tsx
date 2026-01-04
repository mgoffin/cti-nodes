import { useRef } from 'react'
import useTextSelection from '../hooks/useTextSelection'
import SelectionPopover from './SelectionPopover'
import HighlightedContent from './HighlightedContent'
import type { Extracted } from '../types'

interface SelectableContentProps {
  nodeId: string
  content: string
  extracted: Extracted[]
  className?: string
}

export default function SelectableContent({
  nodeId,
  content,
  extracted,
  className = '',
}: SelectableContentProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const { selectedText, selectionRect, clearSelection, setInteracting } =
    useTextSelection(containerRef)

  return (
    <div ref={containerRef} className={className}>
      <HighlightedContent content={content} extracted={extracted} />
      {selectedText && selectionRect && (
        <SelectionPopover
          nodeId={nodeId}
          selectedText={selectedText}
          rect={selectionRect}
          onClose={clearSelection}
          setInteracting={setInteracting}
        />
      )}
    </div>
  )
}
