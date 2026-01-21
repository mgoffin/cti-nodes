import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { tagsApi } from '../api/client'
import type { Tag, TagSuggestion } from '../types'
import ClickableTag from './ClickableTag'

interface TagManagerProps {
  nodeId: string
  tags: Tag[]
}

const SYSTEM_TAGS = ['source', 'datetime']

export default function TagManager({ nodeId, tags }: TagManagerProps) {
  const queryClient = useQueryClient()
  const [editingTag, setEditingTag] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagValue, setNewTagValue] = useState('')

  // Get tag autocomplete suggestions
  const { data: suggestions } = useQuery({
    queryKey: ['tagSuggestions'],
    queryFn: () => tagsApi.getSuggestions(),
  })

  // Get AI tag suggestions for this node
  const { data: nodeSuggestionsData } = useQuery({
    queryKey: ['tagNodeSuggestions', nodeId],
    queryFn: () => tagsApi.getNodeSuggestions(nodeId),
    enabled: !!nodeId,
  })

  // Separate system tags from custom tags
  const sourceTag = tags.find(t => t.name === 'source')
  const customTags = tags.filter(t => !SYSTEM_TAGS.includes(t.name))

  // Mutations
  const addMutation = useMutation({
    mutationFn: (tag: { name: string; value: string }) =>
      tagsApi.addToNode(nodeId, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      toast.success('Tag added')
      setNewTagName('')
      setNewTagValue('')
      setShowAddForm(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add tag')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ tagId, value }: { tagId: string; value: string }) =>
      tagsApi.update(tagId, { value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      toast.success('Tag updated')
      setEditingTag(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update tag')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (tagId: string) => tagsApi.delete(tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      toast.success('Tag deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete tag')
    },
  })

  const acceptTagSuggestionMutation = useMutation({
    mutationFn: (suggestion: TagSuggestion) =>
      tagsApi.addToNode(nodeId, { name: suggestion.tag_name, value: suggestion.tag_value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Tag added')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add tag')
    },
  })

  const rejectTagSuggestionMutation = useMutation({
    mutationFn: (suggestion: TagSuggestion) =>
      tagsApi.rejectSuggestion({
        node_id: nodeId,
        tag_name: suggestion.tag_name,
        tag_value: suggestion.tag_value,
        reason: suggestion.reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Suggestion dismissed')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to dismiss suggestion')
    },
  })

  const handleAcceptAll = async () => {
    if (!nodeSuggestionsData?.suggestions || nodeSuggestionsData.suggestions.length === 0) return

    try {
      for (const suggestion of nodeSuggestionsData.suggestions) {
        await tagsApi.addToNode(nodeId, {
          name: suggestion.tag_name,
          value: suggestion.tag_value
        })
      }
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success(`Added ${nodeSuggestionsData.suggestions.length} tags`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add all tags')
    }
  }

  const handleRejectAll = async () => {
    if (!nodeSuggestionsData?.suggestions || nodeSuggestionsData.suggestions.length === 0) return

    try {
      for (const suggestion of nodeSuggestionsData.suggestions) {
        await tagsApi.rejectSuggestion({
          node_id: nodeId,
          tag_name: suggestion.tag_name,
          tag_value: suggestion.tag_value,
          reason: suggestion.reason,
        })
      }
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('All suggestions dismissed')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to dismiss all suggestions')
    }
  }

  const handleStartEdit = (tag: Tag) => {
    setEditingTag(tag.id)
    setEditValue(tag.value)
  }

  const handleSaveEdit = (tagId: string) => {
    if (editValue.trim()) {
      updateMutation.mutate({ tagId, value: editValue.trim() })
    }
  }

  const handleCancelEdit = () => {
    setEditingTag(null)
    setEditValue('')
  }

  const handleAddTag = () => {
    if (newTagName.trim() && newTagValue.trim()) {
      addMutation.mutate({ name: newTagName.trim(), value: newTagValue.trim() })
    }
  }

  const handleDelete = (tagId: string) => {
    if (confirm('Delete this tag?')) {
      deleteMutation.mutate(tagId)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold theme-text-heading">Tags</h2>
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="icon-btn"
            title="Add tag"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        )}
      </div>

      <div className="space-y-2">
        {/* Source tag - read only but clickable */}
        {sourceTag && (
          <div className="flex items-center gap-2">
            <ClickableTag
              tag={sourceTag}
              variant="source"
              showName={true}
            />
            <span className="text-xs theme-text-muted">(system)</span>
          </div>
        )}

        {/* Custom tags - editable */}
        {customTags.map((tag) => (
          <div key={tag.id} className="flex items-center gap-2">
            {editingTag === tag.id ? (
              // Edit mode
              <div className="flex items-center gap-2 flex-1">
                <span className="text-sm theme-text-muted">{tag.name}:</span>
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="input inline-edit-input flex-1 px-2"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveEdit(tag.id)
                    if (e.key === 'Escape') handleCancelEdit()
                  }}
                />
                <button
                  onClick={() => handleSaveEdit(tag.id)}
                  className="icon-btn"
                  title="Save"
                  disabled={updateMutation.isPending}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="icon-btn"
                  title="Cancel"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              // Display mode
              <>
                <ClickableTag tag={tag} variant="custom" />
                <button
                  onClick={() => handleStartEdit(tag)}
                  className="icon-btn"
                  title="Edit tag"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button
                  onClick={() => handleDelete(tag.id)}
                  className="icon-btn icon-btn-danger"
                  title="Delete tag"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </>
            )}
          </div>
        ))}

        {/* Add tag form */}
        {showAddForm && (
          <div className="mt-4 p-3 rounded-lg theme-bg-code">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <label className="block text-xs theme-text-muted mb-1">Name</label>
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  className="input w-full px-2 text-sm"
                  placeholder="e.g., campaign"
                  list="tag-names-add"
                  autoFocus
                />
                <datalist id="tag-names-add">
                  {suggestions?.names
                    .filter(n => !SYSTEM_TAGS.includes(n))
                    .map((name) => (
                      <option key={name} value={name} />
                    ))}
                </datalist>
              </div>
              <div className="flex-1">
                <label className="block text-xs theme-text-muted mb-1">Value</label>
                <input
                  type="text"
                  value={newTagValue}
                  onChange={(e) => setNewTagValue(e.target.value)}
                  className="input w-full px-2 text-sm"
                  placeholder="e.g., APT29"
                  list="tag-values-add"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddTag()
                    }
                    if (e.key === 'Escape') setShowAddForm(false)
                  }}
                />
                <datalist id="tag-values-add">
                  {suggestions?.values.map((value) => (
                    <option key={value} value={value} />
                  ))}
                </datalist>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => setShowAddForm(false)}
                className="btn btn-secondary text-sm py-1"
              >
                Cancel
              </button>
              <button
                onClick={handleAddTag}
                className="btn btn-primary text-sm py-1"
                disabled={!newTagName.trim() || !newTagValue.trim() || addMutation.isPending}
              >
                {addMutation.isPending ? 'Adding...' : 'Add Tag'}
              </button>
            </div>
          </div>
        )}

        {/* Empty state */}
        {customTags.length === 0 && !showAddForm && (
          <p className="text-sm theme-text-muted">No custom tags</p>
        )}

        {/* Tag suggestions */}
        {nodeSuggestionsData?.suggestions && nodeSuggestionsData.suggestions.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-2 pr-2">
              <h3 className="text-sm font-medium theme-text-muted flex items-center gap-1">
                <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Suggested Tags
              </h3>
              <div className="flex gap-1">
                <button
                  onClick={handleAcceptAll}
                  className="suggestion-btn-accept"
                  title="Accept all suggestions"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={handleRejectAll}
                  className="suggestion-btn-reject"
                  title="Reject all suggestions"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="space-y-2">
              {nodeSuggestionsData.suggestions.map((suggestion) => (
                <TagSuggestionBanner
                  key={`${suggestion.tag_name}-${suggestion.tag_value}`}
                  suggestion={suggestion}
                  onAccept={() => acceptTagSuggestionMutation.mutate(suggestion)}
                  onReject={() => rejectTagSuggestionMutation.mutate(suggestion)}
                  isLoading={acceptTagSuggestionMutation.isPending || rejectTagSuggestionMutation.isPending}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Tag suggestion banner component
interface TagSuggestionBannerProps {
  suggestion: TagSuggestion
  onAccept: () => void
  onReject: () => void
  isLoading: boolean
}

function TagSuggestionBanner({ suggestion, onAccept, onReject, isLoading }: TagSuggestionBannerProps) {
  return (
    <div className="p-2 rounded-md border suggestion-banner">
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="tag tag-default text-xs">
              {suggestion.tag_name}: {suggestion.tag_value}
            </span>
            <span className="text-xs suggestion-confidence">
              {Math.round(suggestion.confidence * 100)}% confidence
            </span>
          </div>
          <p className="text-xs suggestion-reason mt-1">{suggestion.reason}</p>
        </div>
        {/* Action buttons */}
        <div className="flex gap-1 flex-shrink-0">
          <button
            onClick={onAccept}
            disabled={isLoading}
            className="suggestion-btn-accept"
            title="Add this tag"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
          <button
            onClick={onReject}
            disabled={isLoading}
            className="suggestion-btn-reject"
            title="Dismiss suggestion"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
