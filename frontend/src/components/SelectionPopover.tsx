import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { extractedApi } from '../api/client'
import Combobox from './Combobox'
import { formatTypeName } from '../utils/formatters'

interface SelectionPopoverProps {
  nodeId: string
  selectedText: string
  rect: DOMRect
  onClose: () => void
  setInteracting: (value: boolean) => void
}

export default function SelectionPopover({
  nodeId,
  selectedText,
  rect,
  onClose,
  setInteracting,
}: SelectionPopoverProps) {
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState(false)
  const [selectedType, setSelectedType] = useState('')
  const [capturedText, setCapturedText] = useState(selectedText)

  // Capture the text when expanding so we don't lose it when selection clears
  const handleExpand = () => {
    setCapturedText(selectedText)
    setInteracting(true)
    setExpanded(true)
  }

  // Wrapper to reset interacting state when closing
  const handleClose = () => {
    setInteracting(false)
    onClose()
  }

  // Use captured text once expanded
  const textToAdd = expanded ? capturedText : selectedText

  // Get available entity types
  const { data: entityTypes } = useQuery({
    queryKey: ['extractedTypes'],
    queryFn: () => extractedApi.getTypes(),
  })

  const addMutation = useMutation({
    mutationFn: (entity: { type: string; value: string }) =>
      extractedApi.addToNode(nodeId, entity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Entity added')
      handleClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add entity')
    },
  })

  const handleAdd = () => {
    if (selectedType.trim() && textToAdd) {
      addMutation.mutate({ type: selectedType.trim(), value: textToAdd })
    }
  }

  // Position the popover above the selection
  const style: React.CSSProperties = {
    position: 'fixed',
    left: rect.left + rect.width / 2,
    top: rect.top - 8,
    transform: 'translate(-50%, -100%)',
    zIndex: 100,
  }

  return (
    <div className="selection-popover" style={style}>
      {!expanded ? (
        // Collapsed state - just the + button
        <button
          onMouseDown={(e) => {
            e.preventDefault()
            e.stopPropagation()
            handleExpand()
          }}
          className="flex items-center justify-center w-8 h-8 rounded-full theme-bg-card shadow-lg border theme-border hover:scale-110 transition-transform cursor-pointer"
          title="Add as entity"
        >
          <svg className="w-5 h-5 theme-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      ) : (
        // Expanded state - type input with suggestions
        <div className="flex items-center gap-2 p-2 rounded-lg theme-bg-card shadow-lg border theme-border">
          <Combobox
            value={selectedType}
            onChange={setSelectedType}
            options={entityTypes || []}
            placeholder="Type..."
            className="min-w-[140px]"
            autoFocus
            formatOption={formatTypeName}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && selectedType.trim()) {
                e.preventDefault()
                handleAdd()
              }
              if (e.key === 'Escape') handleClose()
            }}
          />
          <button
            onClick={handleAdd}
            className="icon-btn"
            title="Add entity"
            disabled={!selectedType.trim() || addMutation.isPending}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
          <button
            onClick={handleClose}
            className="icon-btn"
            title="Cancel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
