import { useState } from 'react'
import { useSearchParams, Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { nodesApi, searchApi } from '../api/client'
import NodeList from './NodeList'
import GraphView from './GraphView'
import ExportButton from './ExportButton'

type ViewMode = 'list' | 'graph'

export default function Dashboard() {
  const [searchParams] = useSearchParams()
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set())
  const searchQuery = searchParams.get('q')

  // Fetch nodes or search results
  const { data: nodes, isLoading, error } = useQuery({
    queryKey: ['nodes', searchQuery],
    queryFn: async () => {
      if (searchQuery) {
        const result = await searchApi.search(searchQuery)
        return result.nodes
      }
      return nodesApi.list()
    },
  })

  const handleSelectionChange = (nodeId: string, selected: boolean) => {
    setSelectedNodeIds(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(nodeId)
      } else {
        newSet.delete(nodeId)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (!nodes) return
    
    if (selectedNodeIds.size === nodes.length) {
      setSelectedNodeIds(new Set())
    } else {
      setSelectedNodeIds(new Set(nodes.map(n => n.id)))
    }
  }

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode)
    if (selectionMode) {
      setSelectedNodeIds(new Set())
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-node-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
        <p className="text-red-700 dark:text-red-400">Error loading nodes. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with view toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold theme-text-heading">
            {searchQuery ? `Search: "${searchQuery}"` : 'All Nodes'}
          </h1>
          <p className="theme-text-muted mt-1">
            {nodes?.length || 0} node{nodes?.length !== 1 ? 's' : ''}
            {selectionMode && selectedNodeIds.size > 0 && (
              <span> • {selectedNodeIds.size} selected</span>
            )}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          {/* Export button (when nodes selected) */}
          {selectionMode && selectedNodeIds.size > 0 && (
            <ExportButton nodeIds={Array.from(selectedNodeIds)} />
          )}

          {/* Selection mode toggle */}
          {nodes && nodes.length > 0 && viewMode === 'list' && (
            <button
              onClick={toggleSelectionMode}
              className={`btn ${selectionMode ? 'btn-primary' : 'btn-secondary'}`}
            >
              {selectionMode ? 'Cancel' : 'Select Nodes'}
            </button>
          )}

          {/* Select All button (when in selection mode) */}
          {selectionMode && nodes && nodes.length > 0 && (
            <button
              onClick={handleSelectAll}
              className="btn btn-secondary"
            >
              {selectedNodeIds.size === nodes.length ? 'Deselect All' : 'Select All'}
            </button>
          )}

          {/* View Mode Toggle */}
          <div className="flex items-center space-x-1 toggle-container rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'list' ? 'toggle-btn-active' : 'toggle-btn-inactive'
              }`}
            >
              <span className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <span>List</span>
              </span>
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'graph' ? 'toggle-btn-active' : 'toggle-btn-inactive'
              }`}
            >
              <span className="flex items-center space-x-2">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="5" r="3" strokeWidth={2} />
                  <circle cx="5" cy="19" r="3" strokeWidth={2} />
                  <circle cx="19" cy="19" r="3" strokeWidth={2} />
                  <line x1="12" y1="8" x2="5" y2="16" strokeWidth={2} />
                  <line x1="12" y1="8" x2="19" y2="16" strokeWidth={2} />
                </svg>
                <span>Graph</span>
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Empty state */}
      {(!nodes || nodes.length === 0) && (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" viewBox="0 0 100 100">
            <circle cx="50" cy="30" r="12" fill="currentColor"/>
            <circle cx="25" cy="70" r="12" fill="currentColor"/>
            <circle cx="75" cy="70" r="12" fill="currentColor"/>
            <line x1="50" y1="42" x2="25" y2="58" stroke="currentColor" strokeWidth="3"/>
            <line x1="50" y1="42" x2="75" y2="58" stroke="currentColor" strokeWidth="3"/>
            <line x1="37" y1="70" x2="63" y2="70" stroke="currentColor" strokeWidth="3"/>
          </svg>
          <h3 className="text-lg font-medium theme-text-primary mb-2">No nodes yet</h3>
          <p className="theme-text-muted mb-4">Start capturing threat intel by creating your first node.</p>
          <Link to="/new" className="btn btn-primary">
            Create First Node
          </Link>
        </div>
      )}

      {/* Content */}
      {nodes && nodes.length > 0 && (
        viewMode === 'list' ? (
          <NodeList
            nodes={nodes}
            selectable={selectionMode}
            selectedIds={selectedNodeIds}
            onSelectionChange={handleSelectionChange}
          />
        ) : (
          <GraphView nodes={nodes} />
        )
      )}
    </div>
  )
}
