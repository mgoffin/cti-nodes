import { useState, useEffect, useCallback, RefObject, useRef } from 'react'

interface SelectionState {
  text: string
  rect: DOMRect | null
}

export default function useTextSelection(containerRef: RefObject<HTMLElement | null>) {
  const [selection, setSelection] = useState<SelectionState>({ text: '', rect: null })
  const isInteractingRef = useRef(false)

  const handleSelectionChange = useCallback(() => {
    // Don't clear selection if we're interacting with the popover
    if (isInteractingRef.current) {
      return
    }

    const sel = window.getSelection()

    if (!sel || sel.isCollapsed || !sel.rangeCount) {
      setSelection({ text: '', rect: null })
      return
    }

    const range = sel.getRangeAt(0)
    const text = sel.toString().trim()

    // Check if selection is within our container
    if (containerRef.current && !containerRef.current.contains(range.commonAncestorContainer)) {
      setSelection({ text: '', rect: null })
      return
    }

    if (text.length === 0) {
      setSelection({ text: '', rect: null })
      return
    }

    const rect = range.getBoundingClientRect()
    setSelection({ text, rect })
  }, [containerRef])

  const clearSelection = useCallback(() => {
    window.getSelection()?.removeAllRanges()
    setSelection({ text: '', rect: null })
  }, [])

  useEffect(() => {
    document.addEventListener('selectionchange', handleSelectionChange)
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange)
    }
  }, [handleSelectionChange])

  const setInteracting = useCallback((value: boolean) => {
    isInteractingRef.current = value
  }, [])

  return {
    selectedText: selection.text,
    selectionRect: selection.rect,
    clearSelection,
    setInteracting,
  }
}
