import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { extractedApi } from '../api/client'
import type { Extracted } from '../types'
import ClickableExtracted from './ClickableExtracted'
import Combobox from './Combobox'
import { getEntityHighlightColor, getEntityBorderColor } from '../utils/entityColors'
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

  // Group extracted by type, but preserve original index for color matching
  const groupedExtracted = extracted.reduce((acc, e, originalIndex) => {
    if (!acc[e.type]) acc[e.type] = []
    acc[e.type].push({ entity: e, originalIndex })
    return acc
  }, {} as Record<string, Array<{ entity: Extracted; originalIndex: number }>>)

  // Mutations
  const addMutation = useMutation({
    mutationFn: (entity: { type: string; value: string }) =>
      extractedApi.addToNode(nodeId, entity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['node', nodeId] })
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
      toast.success('Entity deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete entity')
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

  const formatTypeName = (type: string) => {
    return type
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
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
        {Object.entries(groupedExtracted).map(([type, items]) => (
          <div key={type}>
            <h3 className="text-sm font-medium theme-text-muted mb-2">
              {formatTypeName(type)}
            </h3>
            <div className="space-y-2">
              {items.map(({ entity, originalIndex }) => (
                <div key={entity.id} className="flex items-center gap-2">
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
                        options={entityTypes || []}
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
                      {entity.raw_value && entity.raw_value !== entity.value && (
                        <span className="text-xs theme-text-muted" title="Original (defanged)">
                          [{entity.raw_value}]
                        </span>
                      )}
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
                  options={entityTypes || []}
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
      </div>
    </div>
  )
}
