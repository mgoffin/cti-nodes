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
  author?: string // Optional for backward compatibility
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

export interface Comment {
  id: string
  node_id: string
  content: string
  author?: string
  created_at: string
  updated_at: string
}

export interface CommentCreate {
  content: string
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

export interface EntitySuggestion {
  extracted_id: string
  suggestion_type: 'refang' | 'type_change'
  current_value: string
  suggested_value: string | null
  current_type: string
  suggested_type: string | null
  reason: string
}

export interface EntitySuggestionsResponse {
  node_id: string
  suggestions: EntitySuggestion[]
}

export interface RejectSuggestionRequest {
  extracted_id: string
  suggestion_type: string
  suggested_value?: string | null
  suggested_type?: string | null
}

export interface ExtractedEntitySuggestion {
  type: string
  value: string
  reason: string
  source_node_id: string
  confidence: number
}

export interface ExtractedEntitySuggestionsResponse {
  node_id: string
  suggestions: ExtractedEntitySuggestion[]
}

export interface RejectExtractedEntitySuggestionRequest {
  node_id: string
  entity_type: string
  entity_value: string
  reason: string
}

export interface TagSuggestion {
  tag_name: string
  tag_value: string
  reason: string
  confidence: number
}

export interface TagSuggestionsResponse {
  node_id: string
  suggestions: TagSuggestion[]
}

export interface RejectTagSuggestionRequest {
  node_id: string
  tag_name: string
  tag_value: string
  reason: string
}

// Auth types
export type UserRole = 'administrator' | 'analyst' | 'viewer'

export interface User {
  id: string
  username: string
  email: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  last_login: string | null
}

export interface Session {
  id: string
  user_id: string
  created_at: string
  last_accessed: string
  ip_address: string | null
  user_agent: string | null
}

export interface AuthConfig {
  auth_enabled: boolean
  sso_provider: string | null
  sso_display_name: string | null
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface UserProfile {
  display_name_override: string | null
  avatar_url: string | null
  theme_preference: 'light' | 'dark' | 'system' | null
}

export interface UserUpdate {
  role?: UserRole
  is_active?: boolean
}

export interface ProfileUpdate {
  display_name_override?: string | null
  avatar_url?: string | null
  theme_preference?: 'light' | 'dark' | 'system' | null
}

// Export types
export interface ExportOptions {
  format: 'json' | 'csv' | 'stix'
  include_tags: boolean
  include_system_tags: boolean
  include_extracted: boolean
  include_edges: boolean
  include_comments: boolean
  include_related_nodes: boolean
  related_depth: number
  entity_types: string[] | null
}

export interface ExportPreview {
  node_count: number
  tag_count: number
  entity_count: number
  edge_count: number
  comment_count: number
  related_node_count: number
  estimated_size_kb: number
  warnings: string[]
}
