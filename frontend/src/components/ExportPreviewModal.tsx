import { useState, useEffect } from 'react'
import { exportApi } from '../api/client'
import type { ExportOptions } from '../types'
import { formatTypeName } from '../utils/formatters'

interface ExportPreviewModalProps {
  nodeIds: string[]
  options: ExportOptions
  onExport: (options: ExportOptions) => void
  onCancel: () => void
}

const ENTITY_TYPES = [
  'ipv4',
  'ipv6',
  'domain',
  'url',
  'email',
  'hash',
  'cve',
  'malware',
  'threat_actor',
  'tool',
]

// Sort entity types alphabetically by their display names
const SORTED_ENTITY_TYPES = [...ENTITY_TYPES].sort((a, b) => 
  formatTypeName(a).localeCompare(formatTypeName(b))
)

export default function ExportPreviewModal({ nodeIds, options: initialOptions, onExport, onCancel }: ExportPreviewModalProps) {
  const [options, setOptions] = useState<ExportOptions>(initialOptions)
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<string[]>([])

  useEffect(() => {
    // Select all entity types by default
    if (selectedEntityTypes.length === 0) {
      setSelectedEntityTypes(ENTITY_TYPES)
    }
  }, [selectedEntityTypes.length])

  const handleEntityTypeToggle = (type: string) => {
    const newTypes = selectedEntityTypes.includes(type)
      ? selectedEntityTypes.filter(t => t !== type)
      : [...selectedEntityTypes, type]
    
    setSelectedEntityTypes(newTypes)
    setOptions({
      ...options,
      entity_types: newTypes.length === ENTITY_TYPES.length ? null : newTypes,
    })
  }

  const handleSelectAllEntityTypes = () => {
    const allSelected = selectedEntityTypes.length === ENTITY_TYPES.length
    if (allSelected) {
      setSelectedEntityTypes([])
      setOptions({ ...options, entity_types: [] })
    } else {
      setSelectedEntityTypes(ENTITY_TYPES)
      setOptions({ ...options, entity_types: null })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="export-modal rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 export-modal-header border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold export-modal-text">
              Export Options
            </h2>
            <button
              onClick={onCancel}
              className="export-modal-close-btn"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-sm export-modal-text-muted mt-1">
            Format: <span className="font-medium uppercase">{options.format}</span>
          </p>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-6 export-modal-content">
          {/* Export options */}
          <div className="space-y-4">
            <h3 className="font-medium export-modal-text">Export Options</h3>

            {/* Include options */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_tags}
                  onChange={(e) => setOptions({ ...options, include_tags: e.target.checked })}
                  className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                />
                <span className="text-sm export-modal-text-secondary">Include tags</span>
              </label>

              {options.include_tags && (
                <label className="flex items-center space-x-2 cursor-pointer ml-6">
                  <input
                    type="checkbox"
                    checked={options.include_system_tags}
                    onChange={(e) => setOptions({ ...options, include_system_tags: e.target.checked })}
                    className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                  />
                  <span className="text-sm export-modal-text-secondary">Include system tags</span>
                </label>
              )}

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_extracted}
                  onChange={(e) => setOptions({ ...options, include_extracted: e.target.checked })}
                  className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                />
                <span className="text-sm export-modal-text-secondary">Include extracted entities</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_edges}
                  onChange={(e) => setOptions({ ...options, include_edges: e.target.checked })}
                  className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                />
                <span className="text-sm export-modal-text-secondary">Include edges/relationships</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_comments}
                  onChange={(e) => setOptions({ ...options, include_comments: e.target.checked })}
                  className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                />
                <span className="text-sm export-modal-text-secondary">Include comments</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_related_nodes}
                  onChange={(e) => setOptions({ ...options, include_related_nodes: e.target.checked })}
                  className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                />
                <span className="text-sm export-modal-text-secondary">Include related nodes</span>
              </label>

              {options.include_related_nodes && (
                <div className="ml-6 flex items-center space-x-2">
                  <label className="text-sm export-modal-text-secondary">Depth:</label>
                  <select
                    value={options.related_depth}
                    onChange={(e) => setOptions({ ...options, related_depth: parseInt(e.target.value) })}
                    className="input rounded px-3 py-1.5 text-sm focus:ring-2 focus:ring-node-500 focus:border-transparent w-20"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                  </select>
                </div>
              )}
            </div>

            {/* Entity type filter */}
            {options.include_extracted && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium export-modal-text-secondary">
                    Entity Types
                  </label>
                  <button
                    onClick={handleSelectAllEntityTypes}
                    className="text-xs text-node-600 hover:text-node-700"
                  >
                    {selectedEntityTypes.length === ENTITY_TYPES.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {SORTED_ENTITY_TYPES.map(type => (
                    <label key={type} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedEntityTypes.includes(type)}
                        onChange={() => handleEntityTypeToggle(type)}
                        className="rounded border-slate-300 text-node-600 focus:ring-node-500"
                      />
                      <span className="text-sm export-modal-text-secondary">
                        {formatTypeName(type)}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Preview loading state */}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 export-modal-footer border-t px-6 py-4 flex items-center justify-end space-x-3">
          <button
            onClick={onCancel}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={() => onExport(options)}
            className="btn btn-primary"
          >
            Export
          </button>
        </div>
      </div>
    </div>
  )
}