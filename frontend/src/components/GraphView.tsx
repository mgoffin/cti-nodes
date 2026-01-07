import { useEffect, useRef, useState, useMemo } from 'react'
import { useNavigate } from 'react-router'
import CytoscapeComponent from 'react-cytoscapejs'
import type { Core, ElementDefinition } from 'cytoscape'
import { useQuery } from '@tanstack/react-query'
import { nodesApi } from '../api/client'
import type { Node, NodeWithRelations } from '../types'
import { useTheme } from '../hooks/useTheme'

// Colors for different entity types
const ENTITY_COLORS: Record<string, { bg: string; border: string }> = {
  ipv4: { bg: '#f59e0b', border: '#d97706' },      // amber
  ipv6: { bg: '#f59e0b', border: '#d97706' },      // amber
  domain: { bg: '#10b981', border: '#059669' },    // emerald
  url: { bg: '#3b82f6', border: '#2563eb' },       // blue
  email: { bg: '#8b5cf6', border: '#7c3aed' },     // violet
  hash_md5: { bg: '#ec4899', border: '#db2777' },  // pink
  hash_sha1: { bg: '#ec4899', border: '#db2777' }, // pink
  hash_sha256: { bg: '#ec4899', border: '#db2777' }, // pink
  cve: { bg: '#ef4444', border: '#dc2626' },       // red
  tag: { bg: '#06b6d4', border: '#0891b2' },       // cyan
  default: { bg: '#6b7280', border: '#4b5563' },   // gray
}

function getEntityColor(type: string): { bg: string; border: string } {
  return ENTITY_COLORS[type] || ENTITY_COLORS.default
}

interface GraphViewProps {
  nodes: (Node | NodeWithRelations)[]
  centerNodeId?: string
  initialDepth?: number
}

export default function GraphView({ nodes, centerNodeId, initialDepth = 1 }: GraphViewProps) {
  const navigate = useNavigate()
  const cyRef = useRef<Core | null>(null)
  const [depth, setDepth] = useState(initialDepth)
  const [_selectedNodeId, setSelectedNodeId] = useState<string | null>(centerNodeId || null)
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  // Check if we need to fetch full node data for depth 3
  // If any node doesn't have related_nodes, we need to fetch them
  const needsFullData = depth >= 3 && nodes.some(n => !('related_nodes' in n))

  // Fetch full node data when depth >= 3 and we don't have related_nodes
  const { data: fullNodes } = useQuery({
    queryKey: ['nodes-full', nodes.map(n => n.id)],
    queryFn: async () => {
      // Fetch each node with full relations
      const results = await Promise.all(
        nodes.map(n => nodesApi.get(n.id))
      )
      return results
    },
    enabled: needsFullData,
    staleTime: 30000, // Cache for 30 seconds
  })

  // Use full nodes if available and needed, otherwise use passed nodes
  const graphNodes = (needsFullData && fullNodes) ? fullNodes : nodes

  // Depth controls what is shown:
  // 1: Only content nodes
  // 2: Content nodes + their tags/entities
  // 3+: Content nodes + tags/entities + other nodes sharing those tags/entities

  // Build graph elements based on depth
  const elements = useMemo(() => {
    const els: ElementDefinition[] = []
    const addedIds = new Set<string>()
    const entityToNodes = new Map<string, Set<string>>() // Track which nodes have each entity/tag

    // Helper to add a content node
    const addContentNode = (node: Node, type: 'main' | 'related') => {
      if (addedIds.has(node.id)) return
      addedIds.add(node.id)
      els.push({
        data: {
          id: node.id,
          label: node.content.substring(0, 30) + (node.content.length > 30 ? '...' : ''),
          type,
          nodeType: 'content',
        },
      })
    }

    // Helper to add entity/tag node
    const addEntityNode = (entityId: string, label: string, nodeType: 'entity' | 'tag', entityType?: string) => {
      if (addedIds.has(entityId)) return
      addedIds.add(entityId)
      const colors = getEntityColor(nodeType === 'tag' ? 'tag' : (entityType || 'default'))
      els.push({
        data: {
          id: entityId,
          label: label.length > 20 ? label.substring(0, 20) + '...' : label,
          type: nodeType,
          nodeType,
          entityType,
          bgColor: colors.bg,
          borderColor: colors.border,
        },
      })
    }

    // Helper to add edge
    const addEdge = (source: string, target: string, edgeType: string) => {
      const edgeId = `edge-${source}-${target}`
      if (addedIds.has(edgeId)) return
      addedIds.add(edgeId)
      els.push({
        data: {
          id: edgeId,
          source,
          target,
          edgeType,
        },
      })
    }

    // Skip metadata tags
    const skipTags = ['source', 'created_at', 'updated_at', 'datetime', 'date', 'time', 'timestamp']

    // Depth 1: Just the content nodes
    graphNodes.forEach((node) => {
      addContentNode(node, 'main')

      // Build entity/tag to node mapping for depth 3+
      if (node.extracted) {
        node.extracted.forEach((entity) => {
          const entityId = `entity-${entity.type}-${entity.value}`
          if (!entityToNodes.has(entityId)) {
            entityToNodes.set(entityId, new Set())
          }
          entityToNodes.get(entityId)!.add(node.id)
        })
      }
      if (node.tags) {
        node.tags.forEach((tag) => {
          if (skipTags.includes(tag.name.toLowerCase())) return
          const tagId = `tag-${tag.name}-${tag.value}`
          if (!entityToNodes.has(tagId)) {
            entityToNodes.set(tagId, new Set())
          }
          entityToNodes.get(tagId)!.add(node.id)
        })
      }
    })

    // Depth 2+: Add entities and tags
    if (depth >= 2) {
      graphNodes.forEach((node) => {
        // Add extracted entities
        if (node.extracted) {
          node.extracted.forEach((entity) => {
            const entityId = `entity-${entity.type}-${entity.value}`
            addEntityNode(entityId, entity.value, 'entity', entity.type)
            addEdge(node.id, entityId, 'entity')
          })
        }

        // Add tags
        if (node.tags) {
          node.tags.forEach((tag) => {
            if (skipTags.includes(tag.name.toLowerCase())) return
            const tagId = `tag-${tag.name}-${tag.value}`
            addEntityNode(tagId, `${tag.name}: ${tag.value}`, 'tag')
            addEdge(node.id, tagId, 'tag')
          })
        }
      })
    }

    // Depth 3+: Show related nodes and their connections
    if (depth >= 3) {
      graphNodes.forEach((node) => {
        // Check if node has related_nodes (NodeWithRelations)
        const nodeWithRelations = node as NodeWithRelations
        if (nodeWithRelations.related_nodes) {
          nodeWithRelations.related_nodes.forEach((relatedNode) => {
            // Add the related node
            addContentNode(relatedNode, 'related')

            // Add its entities and tags
            if (relatedNode.extracted) {
              relatedNode.extracted.forEach((entity) => {
                const entityId = `entity-${entity.type}-${entity.value}`
                addEntityNode(entityId, entity.value, 'entity', entity.type)
                addEdge(relatedNode.id, entityId, 'entity')
              })
            }
            if (relatedNode.tags) {
              relatedNode.tags.forEach((tag) => {
                if (skipTags.includes(tag.name.toLowerCase())) return
                const tagId = `tag-${tag.name}-${tag.value}`
                addEntityNode(tagId, `${tag.name}: ${tag.value}`, 'tag')
                addEdge(relatedNode.id, tagId, 'tag')
              })
            }
          })
        }

        // Also check edges to draw direct connections between nodes
        if (nodeWithRelations.edges) {
          nodeWithRelations.edges.forEach((edge) => {
            // Add edge between content nodes
            const sourceId = edge.source_node_id
            const targetId = edge.target_node_id
            // Only add if both nodes exist in the graph
            if (addedIds.has(sourceId) && addedIds.has(targetId)) {
              addEdge(sourceId, targetId, 'relation')
            }
          })
        }
      })
    }

    return els
  }, [graphNodes, depth])

  // Cytoscape stylesheet - theme-aware colors
  const stylesheet = useMemo(() => [
    // Content nodes (main and related)
    {
      selector: 'node[nodeType="content"]',
      style: {
        'background-color': '#0ea5e9',
        'label': 'data(label)',
        'font-size': '7px',
        'font-weight': '500',
        'color': isDark ? '#e2e8f0' : '#334155',
        'text-wrap': 'wrap',
        'text-max-width': '60px',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': '4px',
        'width': '14px',
        'height': '14px',
        'border-width': '2px',
        'border-color': '#0284c7',
      },
    },
    {
      selector: 'node[type="related"]',
      style: {
        'background-color': isDark ? '#64748b' : '#94a3b8',
        'border-color': isDark ? '#475569' : '#64748b',
        'width': '12px',
        'height': '12px',
      },
    },
    // Entity nodes
    {
      selector: 'node[nodeType="entity"]',
      style: {
        'background-color': 'data(bgColor)',
        'border-color': 'data(borderColor)',
        'label': 'data(label)',
        'font-size': '6px',
        'font-weight': '400',
        'color': isDark ? '#e2e8f0' : '#334155',
        'text-wrap': 'wrap',
        'text-max-width': '50px',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': '3px',
        'width': '8px',
        'height': '8px',
        'border-width': '1.5px',
        'shape': 'diamond',
      },
    },
    // Tag nodes
    {
      selector: 'node[nodeType="tag"]',
      style: {
        'background-color': 'data(bgColor)',
        'border-color': 'data(borderColor)',
        'label': 'data(label)',
        'font-size': '6px',
        'font-weight': '400',
        'color': isDark ? '#e2e8f0' : '#334155',
        'text-wrap': 'wrap',
        'text-max-width': '50px',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': '3px',
        'width': '8px',
        'height': '8px',
        'border-width': '1.5px',
        'shape': 'round-rectangle',
      },
    },
    {
      selector: 'node:selected',
      style: {
        'background-color': '#0369a1',
        'border-width': '3px',
        'border-color': '#38bdf8',
        'width': '18px',
        'height': '18px',
      },
    },
    // Edges
    {
      selector: 'edge',
      style: {
        'width': 1,
        'line-color': isDark ? '#475569' : '#94a3b8',
        'curve-style': 'bezier',
        'opacity': 0.5,
      },
    },
    {
      selector: 'edge[edgeType="entity"]',
      style: {
        'width': 0.75,
        'line-style': 'solid',
        'opacity': 0.4,
      },
    },
    {
      selector: 'edge[edgeType="tag"]',
      style: {
        'width': 0.75,
        'line-style': 'dashed',
        'opacity': 0.4,
      },
    },
    {
      selector: 'edge[edgeType="relation"]',
      style: {
        'width': 2,
        'line-color': '#0ea5e9',
        'line-style': 'solid',
        'opacity': 0.7,
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#0ea5e9',
        'arrow-scale': 0.8,
      },
    },
  ], [isDark])

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId)
  }

  const handleNodeDoubleClick = (nodeId: string) => {
    navigate(`/node/${nodeId}`)
  }

  useEffect(() => {
    if (cyRef.current) {
      const cy = cyRef.current

      // Remove old listeners to avoid duplicates
      cy.off('tap', 'node')
      cy.off('dbltap', 'node')
      cy.off('dragfree', 'node')

      cy.on('tap', 'node', (evt) => {
        const nodeId = evt.target.id()
        // Only set selected for content nodes
        if (evt.target.data('nodeType') === 'content') {
          handleNodeClick(nodeId)
        }
      })

      cy.on('dbltap', 'node', (evt) => {
        const nodeId = evt.target.id()
        // Only navigate for content nodes
        if (evt.target.data('nodeType') === 'content') {
          handleNodeDoubleClick(nodeId)
        }
      })

      // Re-run layout when a node is dragged to avoid overlaps
      cy.on('dragfree', 'node', (evt) => {
        const draggedNode = evt.target
        // Lock the dragged node in place
        draggedNode.lock()

        // Run layout on other nodes to adjust around the dragged node
        cy.layout({
          name: 'cose',
          animate: true,
          animationDuration: 250,
          nodeRepulsion: () => 12000,
          idealEdgeLength: () => 60,
          edgeElasticity: () => 120,
          nestingFactor: 0.1,
          gravity: 0.2,
          numIter: 400,
          initialTemp: 100,
          coolingFactor: 0.95,
          minTemp: 1.0,
          fit: false, // Don't re-fit, keep current view
          nodeOverlap: 20, // Minimum space between nodes
        } as any).run()

        // Unlock the node after layout completes
        setTimeout(() => {
          draggedNode.unlock()
        }, 280)
      })

      // Run initial layout with settings optimized for preventing overlaps
      cy.layout({
        name: 'cose',
        animate: true,
        animationDuration: 400,
        nodeRepulsion: () => 15000,
        idealEdgeLength: () => 70,
        edgeElasticity: () => 120,
        nestingFactor: 0.1,
        gravity: 0.2,
        numIter: 800,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
        nodeOverlap: 20, // Minimum space between nodes
        fit: true, // Auto-fit to viewport
        padding: 80, // Padding around the graph
      } as any).run()

      // Center after layout completes
      setTimeout(() => {
        cy.center()
      }, 450)
    }
  }, [elements.length, depth])

  // Depth level descriptions
  const depthDescriptions: Record<number, string> = {
    1: 'Nodes only',
    2: 'Nodes + Entities/Tags',
    3: 'Nodes + Related Nodes',
  }

  return (
    <div className="card p-0 overflow-hidden">
      {/* Controls */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center space-x-4">
          <label className="text-sm text-slate-600 dark:text-slate-400">
            Depth:
            <select
              value={depth}
              onChange={(e) => setDepth(parseInt(e.target.value))}
              className="ml-2 input py-1"
            >
              {[1, 2, 3].map((d) => (
                <option key={d} value={d}>{d} - {depthDescriptions[d]}</option>
              ))}
            </select>
          </label>
          {/* Legend */}
          <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center">
              <span
                className="w-3 h-3 rounded-full mr-1"
                style={{ backgroundColor: '#0ea5e9', border: '2px solid #0284c7' }}
              />
              Node
            </span>
            {depth >= 2 && (
              <>
                <span className="flex items-center">
                  <span
                    className="w-2 h-2 mr-1"
                    style={{
                      backgroundColor: ENTITY_COLORS.ipv4.bg,
                      transform: 'rotate(45deg)',
                    }}
                  />
                  Entity
                </span>
                <span className="flex items-center">
                  <span
                    className="w-2 h-2 rounded-sm mr-1"
                    style={{ backgroundColor: ENTITY_COLORS.tag.bg }}
                  />
                  Tag
                </span>
              </>
            )}
            {depth >= 3 && (
              <span className="flex items-center">
                <span
                  className="w-3 h-3 rounded-full mr-1"
                  style={{ backgroundColor: isDark ? '#64748b' : '#94a3b8', border: `2px solid ${isDark ? '#475569' : '#64748b'}` }}
                />
                Related
              </span>
            )}
          </div>
        </div>
        <div className="text-sm text-slate-500 dark:text-slate-400">
          Click to select, double-click to open
        </div>
      </div>

      {/* Graph */}
      <div
        className="h-[600px] w-full transition-colors duration-200"
        style={{ backgroundColor: isDark ? '#1e293b' : '#ffffff' }}
      >
        <CytoscapeComponent
          key={theme}
          elements={elements}
          stylesheet={stylesheet}
          style={{ width: '100%', height: '100%' }}
          cy={(cy) => { cyRef.current = cy }}
          layout={{ name: 'cose' }}
        />
      </div>
    </div>
  )
}
