import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { commentsApi } from '../api/client'
import type { Comment } from '../types'

interface CommentManagerProps {
  nodeId: string
}

type SortBy = 'created_at' | 'updated_at'
type Order = 'asc' | 'desc'

export default function CommentManager({ nodeId }: CommentManagerProps) {
  const queryClient = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)
  const [newContent, setNewContent] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [sortBy, setSortBy] = useState<SortBy>('created_at')
  const [order, setOrder] = useState<Order>('desc')
  const [previewMode, setPreviewMode] = useState<Record<string, boolean>>({})
  const [showMarkdownHelp, setShowMarkdownHelp] = useState(false)

  // Fetch comments
  const { data: comments = [] } = useQuery({
    queryKey: ['comments', nodeId, sortBy, order],
    queryFn: () => commentsApi.list(nodeId, sortBy, order),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (content: string) => commentsApi.create(nodeId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', nodeId] })
      toast.success('Comment added')
      setNewContent('')
      setShowAddForm(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add comment')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      commentsApi.update(id, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', nodeId] })
      toast.success('Comment updated')
      setEditingId(null)
      setEditContent('')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update comment')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => commentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', nodeId] })
      toast.success('Comment deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete comment')
    },
  })

  const handleSubmit = () => {
    if (newContent.trim()) {
      createMutation.mutate(newContent.trim())
    }
  }

  const handleUpdate = (id: string) => {
    if (editContent.trim()) {
      updateMutation.mutate({ id, content: editContent.trim() })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, action: () => void) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault()
      action()
    }
  }

  const startEdit = (comment: Comment) => {
    setEditingId(comment.id)
    setEditContent(comment.content)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditContent('')
  }

  const togglePreview = (commentId: string) => {
    setPreviewMode((prev) => ({ ...prev, [commentId]: !prev[commentId] }))
  }

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering with extended syntax support
    let html = content
      // Multi-line code blocks (must be processed before inline code)
      .replace(/```([\s\S]*?)```/g, '<pre class="theme-bg-code p-3 rounded overflow-x-auto my-2"><code class="theme-text-primary text-sm">$1</code></pre>')
      // Headings
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mb-2 mt-3">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold mb-2 mt-3">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-semibold mb-2 mt-3">$1</h1>')
      // Horizontal line
      .replace(/^---$/gm, '<hr class="my-3 theme-border" />')
      // Strike-through (must be before bold)
      .replace(/~~(.*?)~~/g, '<del>$1</del>')
      // Bold and italic
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Color syntax: {red}text{/red} or {#ff0000}text{/}
      .replace(/\{(#[0-9a-fA-F]{6}|red|blue|green|yellow|orange|purple|pink|gray)\}(.*?)\{\/\}/g, '<span style="color: $1">$2</span>')
      // Inline code
      .replace(/`(.*?)`/g, '<code class="theme-bg-code px-1.5 py-0.5 rounded theme-text-primary text-sm">$1</code>')
    
    // Process lists (needs special handling for grouping)
    const lines = html.split('\n')
    const processedLines: string[] = []
    let inUnorderedList = false
    let inOrderedList = false
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const unorderedMatch = line.match(/^[-*]\s+(.*)$/)
      const orderedMatch = line.match(/^\d+\.\s+(.*)$/)
      
      if (unorderedMatch) {
        if (!inUnorderedList) {
          processedLines.push('<ul class="list-disc list-inside my-2 ml-4">')
          inUnorderedList = true
        }
        processedLines.push(`<li>${unorderedMatch[1]}</li>`)
      } else if (orderedMatch) {
        if (!inOrderedList) {
          processedLines.push('<ol class="list-decimal list-inside my-2 ml-4">')
          inOrderedList = true
        }
        processedLines.push(`<li>${orderedMatch[1]}</li>`)
      } else {
        if (inUnorderedList) {
          processedLines.push('</ul>')
          inUnorderedList = false
        }
        if (inOrderedList) {
          processedLines.push('</ol>')
          inOrderedList = false
        }
        processedLines.push(line)
      }
    }
    
    // Close any open lists
    if (inUnorderedList) processedLines.push('</ul>')
    if (inOrderedList) processedLines.push('</ol>')
    
    html = processedLines.join('\n')
    
    // Paragraphs
    html = html
      .replace(/\n\n/g, '</p><p class="mb-2">')
      .replace(/\n/g, '<br/>')

    return `<p class="mb-2">${html}</p>`
  }

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  return (
    <div className="card mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold theme-text-heading">
          Comments ({comments.length})
        </h3>
        <div className="flex items-center gap-1">
          {/* Sort buttons */}
          <button
            onClick={() => { setSortBy('created_at'); setOrder('desc'); }}
            className={`icon-btn ${sortBy === 'created_at' && order === 'desc' ? 'opacity-100' : 'opacity-50 hover:opacity-75'}`}
            title="Newest First (Created)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>

          <button
            onClick={() => { setSortBy('created_at'); setOrder('asc'); }}
            className={`icon-btn ${sortBy === 'created_at' && order === 'asc' ? 'opacity-100' : 'opacity-50 hover:opacity-75'}`}
            title="Oldest First (Created)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </button>

          <button
            onClick={() => { setSortBy('updated_at'); setOrder('desc'); }}
            className={`icon-btn ${sortBy === 'updated_at' && order === 'desc' ? 'opacity-100' : 'opacity-50 hover:opacity-75'}`}
            title="Recently Updated"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          <button
            onClick={() => { setSortBy('updated_at'); setOrder('asc'); }}
            className={`icon-btn ${sortBy === 'updated_at' && order === 'asc' ? 'opacity-100' : 'opacity-50 hover:opacity-75'}`}
            title="Least Recently Updated"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          {/* Markdown help button */}
          <div className="relative">
            <button
              onClick={() => setShowMarkdownHelp(!showMarkdownHelp)}
              className="icon-btn"
              title="Markdown help"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>

            {/* Markdown help popup */}
            {showMarkdownHelp && (
              <div className="absolute right-0 top-full mt-2 w-96 card shadow-lg z-50 max-h-[80vh] overflow-y-auto">
                <h4 className="text-sm font-semibold theme-text-heading mb-3">Markdown Syntax</h4>
          <div className="space-y-2 text-sm">
            <div>
              <p className="font-medium theme-text-primary">Headings</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary"># Heading 1</code>
              <span className="theme-text-muted mx-1">•</span>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">## Heading 2</code>
              <span className="theme-text-muted mx-1">•</span>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">### Heading 3</code>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Bold & Italic</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">**bold text**</code>
              <span className="theme-text-muted mx-1">•</span>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">*italic text*</code>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Strike-through</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">~~deleted text~~</code>
              <p className="text-xs theme-text-muted mt-1">Wraps text with tildes for strike-through</p>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Lists</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">- Bullet item</code>
              <span className="theme-text-muted mx-1">•</span>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">* Another bullet</code>
              <br/>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary mt-1">1. Numbered item</code>
              <p className="text-xs theme-text-muted mt-1">Consecutive list items will be grouped</p>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Inline Code</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">`code`</code>
              <p className="text-xs theme-text-muted mt-1">Wraps text in backticks for inline code</p>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Multi-line Code Block</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">```<br/>code block<br/>```</code>
              <p className="text-xs theme-text-muted mt-1">Triple backticks for code blocks</p>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Horizontal Line</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">---</code>
              <p className="text-xs theme-text-muted mt-1">Three dashes on their own line</p>
            </div>

            <div>
              <p className="font-medium theme-text-primary">Color</p>
              <code className="text-xs theme-bg-code px-1.5 py-0.5 rounded theme-text-primary">{'{'}red{'}'}text{'{'}/{'}'}  {'{'}#ff0000{'}'}text{'{'}/{'}'}  </code>
              <p className="text-xs theme-text-muted mt-1">Named colors: red, blue, green, yellow, orange, purple, pink, gray</p>
            </div>
          </div>
          <button
            onClick={() => setShowMarkdownHelp(false)}
            className="mt-3 btn btn-secondary text-sm w-full"
          >
            Close
          </button>
        </div>
      )}
          </div>

          {/* Add button */}
          {!showAddForm && (
            <button
              onClick={() => setShowAddForm(true)}
              className="icon-btn"
              title="Add comment"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Add new comment form */}
      {showAddForm && (
        <div className="mb-4 p-4 theme-bg-hover rounded-lg border theme-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium theme-text-primary">New Comment</span>
            <button
              onClick={() => setPreviewMode({ ...previewMode, new: !previewMode.new })}
              className="text-xs theme-text-muted hover:theme-text-primary"
            >
              {previewMode.new ? 'Edit' : 'Preview'}
            </button>
          </div>

          {previewMode.new ? (
            <div
              className="prose prose-sm max-w-none theme-text-primary mb-3 p-3 theme-bg-card rounded border theme-border"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(newContent) }}
            />
          ) : (
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              onKeyDown={(e) => handleKeyDown(e, handleSubmit)}
              rows={4}
              className="input w-full px-3 resize-y mb-3"
              placeholder="Write your comment... (Markdown supported: **bold**, *italic*, `code`)"
              autoFocus
            />
          )}

          <div className="flex items-center justify-between">
            <span className="text-xs theme-text-muted">
              Ctrl+Enter to submit • Markdown supported
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowAddForm(false)
                  setNewContent('')
                  setPreviewMode({ ...previewMode, new: false })
                }}
                className="btn btn-secondary text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!newContent.trim() || createMutation.isPending}
                className="btn btn-primary text-sm"
              >
                {createMutation.isPending ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments list */}
      {comments.length === 0 ? (
        <p className="text-center theme-text-muted py-8">
          No comments yet. Click the + button to add one.
        </p>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div key={comment.id} className="p-4 theme-bg-hover rounded-lg border theme-border">
              {editingId === comment.id ? (
                // Edit mode
                <>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium theme-text-primary">Edit Comment</span>
                    <button
                      onClick={() => togglePreview(comment.id)}
                      className="text-xs theme-text-muted hover:theme-text-primary"
                    >
                      {previewMode[comment.id] ? 'Edit' : 'Preview'}
                    </button>
                  </div>

                  {previewMode[comment.id] ? (
                    <div
                      className="prose prose-sm max-w-none theme-text-primary mb-3 p-3 theme-bg-card rounded border theme-border"
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(editContent) }}
                    />
                  ) : (
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      onKeyDown={(e) => handleKeyDown(e, () => handleUpdate(comment.id))}
                      rows={4}
                      className="input w-full px-3 resize-y mb-3"
                      autoFocus
                    />
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={cancelEdit}
                      className="btn btn-secondary text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleUpdate(comment.id)}
                      disabled={!editContent.trim() || updateMutation.isPending}
                      className="btn btn-primary text-sm"
                    >
                      {updateMutation.isPending ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </>
              ) : (
                // View mode
                <>
                  <div
                    className="prose prose-sm max-w-none theme-text-primary mb-3"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(comment.content) }}
                  />

                  <div className="flex items-center justify-between text-xs theme-text-muted border-t theme-border pt-2 mt-2">
                    <div className="flex items-center gap-3">
                      <span>
                        <strong>{comment.author || 'Anonymous'}</strong>
                      </span>
                      <span>Created: {formatDateTime(comment.created_at)}</span>
                      {comment.updated_at !== comment.created_at && (
                        <span>• Updated: {formatDateTime(comment.updated_at)}</span>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(comment)}
                        className="hover:theme-text-primary transition-colors"
                        title="Edit comment"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('Are you sure you want to delete this comment?')) {
                            deleteMutation.mutate(comment.id)
                          }
                        }}
                        className="hover:text-red-500 transition-colors"
                        title="Delete comment"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
