import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { exportApi } from '../api/client'
import type { ExportOptions } from '../types'
import ExportPreviewModal from './ExportPreviewModal'

interface ExportButtonProps {
  nodeIds: string[]
  buttonText?: string
  className?: string
}

const DEFAULT_OPTIONS: ExportOptions = {
  format: 'json',
  include_tags: true,
  include_system_tags: true,
  include_extracted: true,
  include_edges: false,
  include_comments: false,
  include_related_nodes: false,
  related_depth: 1,
  entity_types: null,
}

export default function ExportButton({ nodeIds, buttonText = 'Export', className = '' }: ExportButtonProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [options, setOptions] = useState<ExportOptions>(DEFAULT_OPTIONS)

  const exportMutation = useMutation({
    mutationFn: ({ nodeIds, options }: { nodeIds: string[]; options: ExportOptions }) =>
      exportApi.export(nodeIds, options),
    onSuccess: (blob, variables) => {
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      // Generate filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const extension = variables.options.format === 'csv' ? 'csv' : 'json'
      a.download = `nodes_export_${timestamp}.${extension}`
      
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('Export completed')
      setShowMenu(false)
    },
    onError: () => {
      toast.error('Export failed')
    },
  })

  const handleFormatSelect = (format: 'json' | 'csv' | 'stix') => {
    const newOptions = { ...options, format }
    setOptions(newOptions)
    setShowMenu(false)
    setShowPreview(true)
  }

  const handleExport = (finalOptions: ExportOptions) => {
    exportMutation.mutate({ nodeIds, options: finalOptions })
    setShowPreview(false)
  }

  if (nodeIds.length === 0) {
    return null
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className={`btn btn-secondary flex items-center space-x-2 ${className}`}
        disabled={exportMutation.isPending}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <span>{exportMutation.isPending ? 'Exporting...' : buttonText}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-slate-800 ring-1 ring-black ring-opacity-5 z-20">
            <div className="py-1" role="menu">
              <button
                onClick={() => handleFormatSelect('json')}
                className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center space-x-2"
                role="menuitem"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>Export as JSON</span>
              </button>
              <button
                onClick={() => handleFormatSelect('csv')}
                className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center space-x-2"
                role="menuitem"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Export as CSV</span>
              </button>
              <button
                onClick={() => handleFormatSelect('stix')}
                className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center space-x-2"
                role="menuitem"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span>Export as STIX 2.1</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Preview modal */}
      {showPreview && (
        <ExportPreviewModal
          nodeIds={nodeIds}
          options={options}
          onExport={handleExport}
          onCancel={() => setShowPreview(false)}
        />
      )}
    </div>
  )
}
