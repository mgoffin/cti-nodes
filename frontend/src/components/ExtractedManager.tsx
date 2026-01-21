import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { extractedApi } from '../api/client'
import type { Extracted, EntitySuggestion, ExtractedEntitySuggestion } from '../types'
import ClickableExtracted from './ClickableExtracted'
import Combobox from './Combobox'
import { getEntityHighlightColor, getEntityBorderColor } from '../utils/entityColors'
import { formatTypeName } from '../utils/formatters'
import { useTheme } from '../hooks/useTheme'

interface ExtractedManagerProps {
  nodeId: string
  extracted: Extracted[]
}

export default function ExtractedManager({ nodeId, extracted }: ExtractedManagerProps) {
  const queryClient = useQueryClient()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editType, setEditType] = useState('')
  const [editValue, setEditValue] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [newType, setNewType] = useState('')
  const [newValue, setNewValue] = useState('')

  // Get available entity types
  const { data: entityTypes } = useQuery({
    queryKey: ['extractedTypes'],
    queryFn: () => extractedApi.getTypes(),
  })

  // Get entity suggestions
  const { data: suggestionsData } = useQuery({
    queryKey: ['entitySuggestions', nodeId],
    queryFn: () => extractedApi.getSuggestions(nodeId),
    enabled: !!nodeId && extracted.length > 0,
  })

  // Get extracted entity suggestions (new entities from other nodes)
  const { data: entitySuggestionsData } = useQuery({
    queryKey: ['extractedEntitySuggestions', nodeId],
    queryFn: () => extractedApi.getEntitySuggestions(nodeId),
    enabled: !!nodeId,
  })

  // Create a map of suggestions by extracted_id for easy lookup
  const suggestionsByEntityId = suggestionsData?.suggestions.reduce((acc, s) => {
    acc[s.extracted_id] = s
    return acc
  }, {} as Record<string, EntitySuggestion>) || {}

  // Group extracted by type, but preserve original index for color matching
  const groupedExtracted = extracted.reduce((acc, e, originalIndex) => {
    if (!acc[e.type]) acc[e.type] = []
    acc[e.type].push({ entity: e, originalIndex })
    return acc
  }, {} as Record<string, Array<{ entity: Extracted; originalIndex: number }>>)

  // Create sorted array of [type, items] tuples for rendering
  const sortedGroups = Object.entries(groupedExtracted).sort(([typeA], [typeB]) =>
    formatTypeName(typeA).localeCompare(formatTypeName(typeB), undefined, { sensitivity: 'base' })
  )

  // Mutations
  const addMutation = useMutation({
    mutationFn: (entity: { type: string; value: string }) =>
      extractedApi.addToNode(nodeId, entity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Entity added')
      setNewType('')
      setNewValue('')
      setShowAddForm(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add entity')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, type, value }: { id: string; type: string; value: string }) =>
      extractedApi.update(id, { type, value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Entity updated')
      setEditingId(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update entity')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => extractedApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Entity deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete entity')
    },
  })

  const rejectSuggestionMutation = useMutation({
    mutationFn: (suggestion: EntitySuggestion) =>
      extractedApi.rejectSuggestion({
        extracted_id: suggestion.extracted_id,
        suggestion_type: suggestion.suggestion_type,
        suggested_value: suggestion.suggested_value,
        suggested_type: suggestion.suggested_type,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      toast.success('Suggestion dismissed')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to dismiss suggestion')
    },
  })

  const acceptEntitySuggestionMutation = useMutation({
    mutationFn: (suggestion: ExtractedEntitySuggestion) =>
      extractedApi.addToNode(nodeId, { type: suggestion.type, value: suggestion.value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['extractedEntitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success('Entity added')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add entity')
    },
  })

  const rejectEntitySuggestionMutation = useMutation({
    mutationFn: (suggestion: ExtractedEntitySuggestion) =>
      extractedApi.rejectEntitySuggestion({
        node_id: nodeId,
        entity_type: suggestion.type,
        entity_value: suggestion.value,
        reason: suggestion.reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['extractedEntitySuggestions', nodeId] })
      toast.success('Suggestion dismissed')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to dismiss suggestion')
    },
  })

  const handleAcceptAllEntitySuggestions = async () => {
    if (!entitySuggestionsData?.suggestions || entitySuggestionsData.suggestions.length === 0) return
    
    try {
      for (const suggestion of entitySuggestionsData.suggestions) {
        await extractedApi.addToNode(nodeId, { 
          type: suggestion.type, 
          value: suggestion.value 
        })
      }
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['extractedEntitySuggestions', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['tagNodeSuggestions', nodeId] })
      toast.success(`Added ${entitySuggestionsData.suggestions.length} entities`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add all entities')
    }
  }

  const handleRejectAllEntitySuggestions = async () => {
    if (!entitySuggestionsData?.suggestions || entitySuggestionsData.suggestions.length === 0) return
    
    try {
      for (const suggestion of entitySuggestionsData.suggestions) {
        await extractedApi.rejectEntitySuggestion({
          node_id: nodeId,
          entity_type: suggestion.type,
          entity_value: suggestion.value,
          reason: suggestion.reason,
        })
      }
      queryClient.invalidateQueries({ queryKey: ['extractedEntitySuggestions', nodeId] })
      toast.success('All suggestions dismissed')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to dismiss all suggestions')
    }
  }

  const acceptSuggestionMutation = useMutation({
    mutationFn: (suggestion: EntitySuggestion) => {
      const updates: { type?: string; value?: string } = {}
      if (suggestion.suggestion_type === 'refang' && suggestion.suggested_value) {
        updates.value = suggestion.suggested_value
      } else if (suggestion.suggestion_type === 'type_change' && suggestion.suggested_type) {
        updates.type = suggestion.suggested_type
      }
      return extractedApi.update(suggestion.extracted_id, updates)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['entitySuggestions', nodeId] })
      toast.success('Suggestion applied')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to apply suggestion')
    },
  })

  const handleStartEdit = (entity: Extracted) => {
    setEditingId(entity.id)
    setEditType(entity.type)
    setEditValue(entity.value)
  }

  const handleSaveEdit = (id: string) => {
    if (editType.trim() && editValue.trim()) {
      updateMutation.mutate({ id, type: editType.trim(), value: editValue.trim() })
    }
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditType('')
    setEditValue('')
  }

  const handleAdd = () => {
    if (newType.trim() && newValue.trim()) {
      addMutation.mutate({ type: newType.trim(), value: newValue.trim() })
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('Delete this entity?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold theme-text-heading">Extracted Entities</h2>
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="icon-btn"
            title="Add entity"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        )}
      </div>

      <div className="space-y-4">
        {sortedGroups.map(([type, items]) => (
          <div key={type}>
            <h3 className="text-sm font-medium theme-text-muted mb-2">
              {formatTypeName(type)}
            </h3>
            <div className="space-y-2">
              {items.map(({ entity, originalIndex }) => (
                <div key={entity.id}>
                  <div className="flex items-center gap-2">
                    {/* Color indicator dot */}
                    <span
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{
                        backgroundColor: getEntityHighlightColor(originalIndex, isDark),
                        border: `2px solid ${getEntityBorderColor(originalIndex, isDark)}`,
                      }}
                      title="Matches highlighted text in content"
                    />
                    {editingId === entity.id ? (
                    // Edit mode
                    <div className="flex items-center gap-2 flex-1">
                      <Combobox
                        value={editType}
                        onChange={setEditType}
                        options={[...(entityTypes || [])].sort((a, b) => formatTypeName(a).localeCompare(formatTypeName(b), undefined, { sensitivity: 'base' }))}
                        placeholder="Type"
                        className="w-40"
                        formatOption={formatTypeName}
                      />
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="input inline-edit-input flex-1 px-2"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(entity.id)
                          if (e.key === 'Escape') handleCancelEdit()
                        }}
                      />
                      <button
                        onClick={() => handleSaveEdit(entity.id)}
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
                      <ClickableExtracted extracted={entity} />
                      <button
                        onClick={() => handleStartEdit(entity)}
                        className="icon-btn"
                        title="Edit entity"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(entity.id)}
                        className="icon-btn icon-btn-danger"
                        title="Delete entity"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </>
                  )}
                  </div>
                  {/* Display raw_value below if different from value */}
                  {entity.raw_value && entity.raw_value !== entity.value && !editingId && (
                    <div className="ml-5 mt-1">
                      <span className="text-xs theme-text-muted" title="Original (defanged)">
                        [{entity.raw_value}]
                      </span>
                    </div>
                  )}
                  {/* Suggestion banner */}
                  {suggestionsByEntityId[entity.id] && !editingId && (
                    <SuggestionBanner
                      suggestion={suggestionsByEntityId[entity.id]}
                      onAccept={() => acceptSuggestionMutation.mutate(suggestionsByEntityId[entity.id])}
                      onReject={() => rejectSuggestionMutation.mutate(suggestionsByEntityId[entity.id])}
                      isLoading={acceptSuggestionMutation.isPending || rejectSuggestionMutation.isPending}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Add entity form */}
        {showAddForm && (
          <div className="mt-4 p-3 rounded-lg theme-bg-code">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <label className="block text-xs theme-text-muted mb-1">Type</label>
                <Combobox
                  value={newType}
                  onChange={setNewType}
                  options={[...(entityTypes || [])].sort((a, b) => formatTypeName(a).localeCompare(formatTypeName(b), undefined, { sensitivity: 'base' }))}
                  placeholder="e.g., ipv4, domain"
                  autoFocus
                  formatOption={formatTypeName}
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs theme-text-muted mb-1">Value</label>
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  className="input w-full px-2 text-sm"
                  placeholder="e.g., 192.168.1.1"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAdd()
                    }
                    if (e.key === 'Escape') setShowAddForm(false)
                  }}
                />
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
                onClick={handleAdd}
                className="btn btn-primary text-sm py-1"
                disabled={!newType.trim() || !newValue.trim() || addMutation.isPending}
              >
                {addMutation.isPending ? 'Adding...' : 'Add Entity'}
              </button>
            </div>
          </div>
        )}

        {/* Empty state */}
        {extracted.length === 0 && !showAddForm && (
          <p className="text-sm theme-text-muted">No extracted entities</p>
        )}

        {/* Suggested entities */}
        {entitySuggestionsData?.suggestions && entitySuggestionsData.suggestions.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-2 pr-2">
              <h3 className="text-sm font-medium theme-text-muted flex items-center gap-1">
                <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Suggested Entities
              </h3>
              <div className="flex gap-1">
                <button
                  onClick={handleAcceptAllEntitySuggestions}
                  className="suggestion-btn-accept"
                  title="Accept all suggestions"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={handleRejectAllEntitySuggestions}
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
              {entitySuggestionsData.suggestions.map((suggestion) => (
                <EntitySuggestionBanner
                  key={`${suggestion.type}-${suggestion.value}`}
                  suggestion={suggestion}
                  onAccept={() => acceptEntitySuggestionMutation.mutate(suggestion)}
                  onReject={() => rejectEntitySuggestionMutation.mutate(suggestion)}
                  isLoading={acceptEntitySuggestionMutation.isPending || rejectEntitySuggestionMutation.isPending}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Suggestion banner component
interface SuggestionBannerProps {
  suggestion: EntitySuggestion
  onAccept: () => void
  onReject: () => void
  isLoading: boolean
}

function SuggestionBanner({ suggestion, onAccept, onReject, isLoading }: SuggestionBannerProps) {
  return (
    <div className="w-full mt-1 p-2 rounded-md border suggestion-banner">
      <div className="flex items-start gap-2">
        {/* Warning icon */}
        <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div className="flex-1 min-w-0">
          <p className="text-xs suggestion-confidence">
            {suggestion.suggestion_type === 'refang' ? (
              <>
                Suggested fix: <code className="px-1 py-0.5 rounded theme-bg-code font-mono text-xs">{suggestion.suggested_value}</code>
              </>
            ) : (
              <>
                Suggested type: <span className="font-medium">{formatTypeName(suggestion.suggested_type || '')}</span>
              </>
            )}
          </p>
          <p className="text-xs suggestion-reason mt-0.5">{suggestion.reason}</p>
        </div>
        {/* Action buttons */}
        <div className="flex gap-1 flex-shrink-0">
          <button
            onClick={onAccept}
            disabled={isLoading}
            className="suggestion-btn-accept"
            title="Accept suggestion"
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

// Entity suggestion banner component (for new entities from other nodes)
interface EntitySuggestionBannerProps {
  suggestion: ExtractedEntitySuggestion
  onAccept: () => void
  onReject: () => void
  isLoading: boolean
}

function EntitySuggestionBanner({ suggestion, onAccept, onReject, isLoading }: EntitySuggestionBannerProps) {
  return (
    <div className="p-2 rounded-md border suggestion-banner">
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="tag tag-default text-xs">
              {formatTypeName(suggestion.type)}: {suggestion.value}
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
            title="Add this entity"
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
