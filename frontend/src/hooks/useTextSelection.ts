import { useState, useEffect, useCallback, RefObject, useRef } from 'react'

interface SelectionState {
  text: string
  rect: DOMRect | null
}

export default function useTextSelection(containerRef: RefObject<HTMLElement | null>) {
  const [selection, setSelection] = useState<SelectionState>({ text: '', rect: null })
  const isInteractingRef = useRef(false)
  const timeoutRef = useRef<number | null>(null)

  const handleSelectionChange = useCallback(() => {
    // Don't clear selection if we're interacting with the popover
    if (isInteractingRef.current) {
      return
    }

    // Clear any pending timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
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

    // Require at least 2 characters to show the popover
    if (text.length < 2) {
      setSelection({ text: '', rect: null })
      return
    }

    // Debounce the popover appearance by 150ms to prevent flashing while dragging
    timeoutRef.current = window.setTimeout(() => {
      const rect = range.getBoundingClientRect()
      setSelection({ text, rect })
    }, 150)
  }, [containerRef])

  const clearSelection = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    window.getSelection()?.removeAllRanges()
    setSelection({ text: '', rect: null })
  }, [])

  useEffect(() => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
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
