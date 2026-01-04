export interface Tag {
  id: string
  node_id: string
  name: string
  value: string
}

export interface Edge {
  id: string
  source_node_id: string
  target_node_id: string
  edge_type: 'tag_match' | 'ioc_match' | 'entity_match' | 'content_match' | 'manual'
  match_value: string | null
  confidence: number
  created_at: string
}

export interface Extracted {
  id: string
  node_id: string
  type: string
  value: string
  raw_value: string
  canonical_value: string | null
}

export interface Node {
  id: string
  content: string
  created_at: string
  updated_at: string
  tags: Tag[]
  extracted: Extracted[]
}

export interface NodeWithRelations extends Node {
  edges: Edge[]
  related_nodes: Node[]
}

export interface NodeCreate {
  content: string
  source: string
  tags: { name: string; value: string }[]
}

export interface SearchResult {
  nodes: Node[]
  total: number
  query: string
}

export interface TagSuggestions {
  names: string[]
  values: string[]
}

export interface TagCreate {
  name: string
  value: string
}

export interface TagUpdate {
  name?: string
  value?: string
}

export interface ExtractedCreate {
  type: string
  value: string
  raw_value?: string
  canonical_value?: string
}

export interface ExtractedUpdate {
  type?: string
  value?: string
  raw_value?: string
  canonical_value?: string
}
