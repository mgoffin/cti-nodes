import axios from 'axios'
import type {
  Node,
  NodeWithRelations,
  NodeCreate,
  SearchResult,
  TagSuggestions,
  Edge,
  Tag,
  TagCreate,
  TagUpdate,
  Extracted,
  ExtractedCreate,
  ExtractedUpdate,
  EntitySuggestionsResponse,
  RejectSuggestionRequest,
  TagSuggestionsResponse,
  RejectTagSuggestionRequest,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Nodes API
export const nodesApi = {
  list: async (limit = 50, offset = 0): Promise<Node[]> => {
    const { data } = await api.get(`/nodes?limit=${limit}&offset=${offset}`)
    return data
  },

  get: async (id: string): Promise<NodeWithRelations> => {
    const { data } = await api.get(`/nodes/${id}`)
    return data
  },

  create: async (node: NodeCreate): Promise<NodeWithRelations> => {
    const { data } = await api.post('/nodes', node)
    return data
  },

  update: async (id: string, updates: Partial<NodeCreate>): Promise<Node> => {
    const { data } = await api.put(`/nodes/${id}`, updates)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/nodes/${id}`)
  },

  getRelated: async (id: string, depth = 1): Promise<Node[]> => {
    const { data } = await api.get(`/nodes/${id}/related?depth=${depth}`)
    return data
  },
}

// Search API
export const searchApi = {
  search: async (query: string, limit = 50, offset = 0): Promise<SearchResult> => {
    const { data } = await api.post('/search', { query, limit, offset })
    return data
  },
}

// Tags API
export const tagsApi = {
  getSuggestions: async (prefix = ''): Promise<TagSuggestions> => {
    const { data } = await api.get(`/tags/suggestions?prefix=${prefix}`)
    return data
  },

  getNames: async (): Promise<string[]> => {
    const { data } = await api.get('/tags/names')
    return data
  },

  getValues: async (tagName: string): Promise<string[]> => {
    const { data } = await api.get(`/tags/values/${tagName}`)
    return data
  },

  addToNode: async (nodeId: string, tag: TagCreate): Promise<Tag> => {
    const { data } = await api.post(`/tags/node/${nodeId}`, tag)
    return data
  },

  update: async (tagId: string, updates: TagUpdate): Promise<Tag> => {
    const { data } = await api.put(`/tags/${tagId}`, updates)
    return data
  },

  delete: async (tagId: string): Promise<void> => {
    await api.delete(`/tags/${tagId}`)
  },

  getNodeSuggestions: async (nodeId: string): Promise<TagSuggestionsResponse> => {
    const { data } = await api.get(`/tags/suggestions/node/${nodeId}`)
    return data
  },

  rejectSuggestion: async (request: RejectTagSuggestionRequest): Promise<void> => {
    await api.post('/tags/suggestions/reject', request)
  },
}

// Edges API
export const edgesApi = {
  create: async (sourceNodeId: string, targetNodeId: string, edgeType = 'manual'): Promise<Edge> => {
    const { data } = await api.post(`/edges?source_node_id=${sourceNodeId}`, {
      target_node_id: targetNodeId,
      edge_type: edgeType,
      confidence: 1.0,
    })
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/edges/${id}`)
  },
}

// Extracted Entities API
export const extractedApi = {
  getTypes: async (): Promise<string[]> => {
    const { data } = await api.get('/extracted/types')
    return data
  },

  addToNode: async (nodeId: string, entity: ExtractedCreate): Promise<Extracted> => {
    const { data } = await api.post(`/extracted/node/${nodeId}`, entity)
    return data
  },

  update: async (extractedId: string, updates: ExtractedUpdate): Promise<Extracted> => {
    const { data } = await api.put(`/extracted/${extractedId}`, updates)
    return data
  },

  delete: async (extractedId: string): Promise<void> => {
    await api.delete(`/extracted/${extractedId}`)
  },

  getSuggestions: async (nodeId: string): Promise<EntitySuggestionsResponse> => {
    const { data } = await api.get(`/extracted/suggestions/${nodeId}`)
    return data
  },

  rejectSuggestion: async (request: RejectSuggestionRequest): Promise<void> => {
    await api.post('/extracted/suggestions/reject', request)
  },
}

export default api
