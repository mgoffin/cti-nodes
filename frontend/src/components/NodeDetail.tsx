import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { nodesApi } from '../api/client'
import GraphView from './GraphView'
import TagManager from './TagManager'
import ExtractedManager from './ExtractedManager'
import SelectableContent from './SelectableContent'
import ClickableSource from './ClickableSource'
import CommentManager from './CommentManager'
import ExportButton from './ExportButton'

export default function NodeDetail() {
  const { nodeId } = useParams<{ nodeId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [viewMode, setViewMode] = useState<'details' | 'graph'>('details')

  const { data: node, isLoading, error } = useQuery({
    queryKey: ['node', nodeId],
    queryFn: () => nodesApi.get(nodeId!),
    enabled: !!nodeId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => nodesApi.delete(nodeId!),
    onSuccess: () => {
      toast.success('Node deleted')
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      navigate('/')
    },
    onError: () => {
      toast.error('Failed to delete node')
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-node-600"></div>
      </div>
    )
  }

  if (error || !node) {
    return (
      <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
        <p className="text-red-700 dark:text-red-400">Node not found or error loading node.</p>
        <Link to="/" className="btn btn-secondary mt-4">Back to Dashboard</Link>
      </div>
    )
  }

  const sourceTag = node.tags.find(t => t.name === 'source')

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this node? This cannot be undone.')) {
      deleteMutation.mutate()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link to="/" className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 flex items-center space-x-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back</span>
        </Link>

        <div className="flex items-center space-x-2">
          {nodeId && <ExportButton nodeIds={[nodeId]} />}
          <button onClick={handleDelete} className="btn btn-danger">
            Delete
          </button>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex items-center space-x-1 toggle-container rounded-lg p-1 w-fit">
        <button
          onClick={() => setViewMode('details')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'details' ? 'toggle-btn-active' : 'toggle-btn-inactive'
          }`}
        >
          Details
        </button>
        <button
          onClick={() => setViewMode('graph')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'graph' ? 'toggle-btn-active' : 'toggle-btn-inactive'
          }`}
        >
          Graph View
        </button>
      </div>

      {viewMode === 'details' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Content Card */}
            <div className="card">
              <h2 className="text-lg font-semibold theme-text-heading mb-4">Content</h2>
              <SelectableContent
                nodeId={node.id}
                content={node.content}
                extracted={node.extracted}
                className="theme-text-primary whitespace-pre-wrap break-words"
              />
            </div>

            {/* Extracted Entities */}
            <ExtractedManager nodeId={node.id} extracted={node.extracted} />

            {/* Related Nodes */}
            {(() => {
              // Filter out related nodes that are only connected via system or suggested tags
              const systemTags = ['source', 'datetime']
              // Tags that are auto-suggested by the system
              const suggestedTags = ['iocs', 'malware', 'attribution', 'vulnerability', 'mitre_att&ck', 
                                     'report', 'advisory', 'article', 'analysis', 'alert', 'bulletin',
                                     'apt', 'ransomware', 'phishing', 'exploit', 'campaign',
                                     'united_states', 'europe', 'asia', 'middle_east', 'russia', 
                                     'china', 'iran', 'north_korea']
              
              const filteredRelatedNodes = node.related_nodes.filter((relNode) => {
                const edge = node.edges.find(
                  e => e.source_node_id === relNode.id || e.target_node_id === relNode.id
                )
                
                // If no edge found, keep the node (shouldn't happen)
                if (!edge) return true
                
                // Keep manual edges
                if (edge.edge_type === 'manual') return true
                
                // Keep IOC and entity matches
                if (edge.edge_type === 'ioc_match' || edge.edge_type === 'entity_match') return true
                
                // For tag_match edges
                if (edge.edge_type === 'tag_match' && edge.match_value) {
                  const tagName = edge.match_value.split('=')[0]
                  
                  // Keep source tag matches (meaningful - same origin)
                  if (tagName === 'source') return true
                  
                  // Filter out system and suggested tags
                  if (systemTags.includes(tagName) || suggestedTags.includes(tagName)) return false
                  
                  // Keep user-created custom tags
                  return true
                }
                
                // Filter out content_match (too generic)
                if (edge.edge_type === 'content_match') return false
                
                return true
              })
              
              return filteredRelatedNodes.length > 0 && (
                <div className="card">
                  <h2 className="text-lg font-semibold theme-text-heading mb-4">
                    Related Nodes ({filteredRelatedNodes.length})
                  </h2>
                  <div className="space-y-3">
                    {filteredRelatedNodes.map((relNode) => {
                      const edge = node.edges.find(
                        e => e.source_node_id === relNode.id || e.target_node_id === relNode.id
                      )
                      return (
                        <Link
                          key={relNode.id}
                          to={`/node/${relNode.id}`}
                          className="block p-3 rounded-lg related-node-item transition-colors"
                        >
                          <p className="theme-text-primary text-sm line-clamp-2">{relNode.content}</p>
                          {edge && (
                            <div className="flex items-center mt-2 text-xs theme-text-muted">
                              <span className="tag tag-default mr-2">{edge.edge_type}</span>
                              {edge.match_value && (
                                <span>via: {edge.match_value}</span>
                              )}
                              <span className="ml-auto">
                                Confidence: {(edge.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </Link>
                      )
                    })}
                  </div>
                </div>
              )
            })()}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Metadata */}
            <div className="card">
              <h2 className="text-lg font-semibold theme-text-heading mb-4">Metadata</h2>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm theme-text-muted">Author</dt>
                  <dd className="theme-text-primary font-medium">
                    {node.author || 'Anonymous'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm theme-text-muted">Created</dt>
                  <dd className="theme-text-primary">
                    {format(new Date(node.created_at), 'PPpp')}
                  </dd>
                </div>
                {node.updated_at !== node.created_at && (
                  <div>
                    <dt className="text-sm theme-text-muted">Last Updated</dt>
                    <dd className="theme-text-primary">
                      {format(new Date(node.updated_at), 'PPpp')}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm theme-text-muted">Source</dt>
                  <dd className="break-all">
                    {sourceTag ? (
                      <ClickableSource source={sourceTag.value} truncateAt={50} />
                    ) : (
                      <span className="theme-text-primary">Unknown</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm theme-text-muted">Node ID</dt>
                  <dd className="theme-text-muted text-xs font-mono break-all">
                    {node.id}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Tags */}
            <TagManager nodeId={node.id} tags={node.tags} />

            {/* Edges */}
            {(() => {
              // Filter out edges based on system-generated and suggested tags
              const systemTags = ['source', 'datetime']
              // Tags that are auto-suggested by the system
              const suggestedTags = ['iocs', 'malware', 'attribution', 'vulnerability', 'mitre_att&ck', 
                                     'report', 'advisory', 'article', 'analysis', 'alert', 'bulletin',
                                     'apt', 'ransomware', 'phishing', 'exploit', 'campaign',
                                     'united_states', 'europe', 'asia', 'middle_east', 'russia', 
                                     'china', 'iran', 'north_korea']
              
              const filteredEdges = node.edges.filter(edge => {
                // Keep manual edges
                if (edge.edge_type === 'manual') return true
                
                // Keep IOC and entity matches
                if (edge.edge_type === 'ioc_match' || edge.edge_type === 'entity_match') return true
                
                // For tag_match edges
                if (edge.edge_type === 'tag_match' && edge.match_value) {
                  const tagName = edge.match_value.split('=')[0]
                  
                  // Keep source tag matches (meaningful - same origin)
                  if (tagName === 'source') return true
                  
                  // Filter out system and suggested tags
                  if (systemTags.includes(tagName) || suggestedTags.includes(tagName)) return false
                  
                  // Keep user-created custom tags
                  return true
                }
                
                // Filter out content_match (too generic)
                if (edge.edge_type === 'content_match') return false
                
                return true
              })
              
              return filteredEdges.length > 0 && (
                <div className="card">
                  <h2 className="text-lg font-semibold theme-text-heading mb-4">
                    Edges ({filteredEdges.length})
                  </h2>
                  <div className="space-y-2">
                    {filteredEdges.map((edge) => (
                      <div key={edge.id} className="text-sm">
                        <div className="flex items-center justify-between">
                          <span className="tag tag-default">{edge.edge_type}</span>
                          <span className={`text-xs ${
                            edge.confidence >= 0.8 ? 'text-green-600 dark:text-green-400' :
                            edge.confidence >= 0.5 ? 'text-yellow-600 dark:text-yellow-400' : 'text-orange-600 dark:text-orange-400'
                          }`}>
                            {(edge.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        {edge.match_value && (
                          <p className="theme-text-muted text-xs mt-1 truncate">
                            {edge.match_value}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })()}

            {/* Comments */}
            <CommentManager nodeId={node.id} />
          </div>
        </div>
      ) : (
        <GraphView nodes={[node]} centerNodeId={node.id} initialDepth={2} />
      )}
    </div>
  )
}
