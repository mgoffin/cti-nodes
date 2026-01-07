"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Tag Schemas ---


class TagBase(BaseModel):
    """Base tag schema."""

    name: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)


class TagCreate(TagBase):
    """Schema for creating a tag."""

    pass


class Tag(TagBase):
    """Full tag schema with ID."""

    id: str
    node_id: str

    class Config:
        from_attributes = True


# --- Edge Schemas ---


class EdgeBase(BaseModel):
    """Base edge schema."""

    target_node_id: str
    edge_type: str = Field(..., pattern="^(tag_match|ioc_match|entity_match|content_match|manual)$")
    match_value: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class EdgeCreate(EdgeBase):
    """Schema for creating an edge."""

    pass


class Edge(EdgeBase):
    """Full edge schema with IDs."""

    id: str
    source_node_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Extracted Schemas ---


class ExtractedCreate(BaseModel):
    """Schema for creating an extracted entity."""

    type: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    raw_value: Optional[str] = None
    canonical_value: Optional[str] = None


class ExtractedUpdate(BaseModel):
    """Schema for updating an extracted entity."""

    type: Optional[str] = Field(None, min_length=1)
    value: Optional[str] = Field(None, min_length=1)
    raw_value: Optional[str] = None
    canonical_value: Optional[str] = None


class Extracted(BaseModel):
    """Schema for extracted IOCs/entities."""

    id: str
    node_id: str
    type: str  # ipv4, ipv6, domain, url, hash_md5, hash_sha1, hash_sha256, email, threat_actor, malware, tool
    value: str
    raw_value: str
    canonical_value: Optional[str] = None

    class Config:
        from_attributes = True


class TagUpdate(BaseModel):
    """Schema for updating a tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[str] = Field(None, min_length=1)


# --- Node Schemas ---


class NodeBase(BaseModel):
    """Base node schema."""

    content: str = Field(..., min_length=1)


class NodeCreate(NodeBase):
    """Schema for creating a node."""

    source: str = Field(..., min_length=1, description="Source of the information (URL, filepath, person, etc.)")
    tags: list[TagCreate] = Field(default_factory=list, description="Additional custom tags")


class NodeUpdate(BaseModel):
    """Schema for updating a node."""

    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[TagCreate]] = None


class Node(NodeBase):
    """Full node schema."""

    id: str
    created_at: datetime
    updated_at: datetime
    author: Optional[str] = None
    tags: list[Tag] = []
    extracted: list["Extracted"] = []

    class Config:
        from_attributes = True


class NodeWithRelations(Node):
    """Node with related edges and extracted data."""

    edges: list[Edge] = []
    extracted: list[Extracted] = []
    related_nodes: list["Node"] = []


# --- Search Schemas ---


class SearchQuery(BaseModel):
    """Schema for search requests."""

    query: str = Field(..., min_length=1, description="Search query string")
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    """Schema for search results."""

    nodes: list[Node]
    total: int
    query: str


# --- Notification Schemas ---


class LinkNotification(BaseModel):
    """Schema for link discovery notifications."""

    node_id: str
    links_found: int
    edges: list[Edge]
    message: str


# --- Entity Suggestion Schemas ---


class EntitySuggestion(BaseModel):
    """A suggested correction for an extracted entity."""

    extracted_id: str
    suggestion_type: str  # 'refang', 'type_change'
    current_value: str
    suggested_value: Optional[str] = None
    current_type: str = ""
    suggested_type: Optional[str] = None
    reason: str = ""


class EntitySuggestionsResponse(BaseModel):
    """Response containing entity suggestions for a node."""

    node_id: str
    suggestions: list[EntitySuggestion]


class RejectSuggestionRequest(BaseModel):
    """Request to reject a suggestion."""

    extracted_id: str
    suggestion_type: str
    suggested_value: Optional[str] = None
    suggested_type: Optional[str] = None


# --- Tag Suggestion Schemas ---


class TagSuggestionSchema(BaseModel):
    """A suggested tag for a node."""

    tag_name: str
    tag_value: str
    reason: str
    confidence: float = 0.8


class TagSuggestionsResponse(BaseModel):
    """Response containing tag suggestions for a node."""

    node_id: str
    suggestions: list[TagSuggestionSchema]


class RejectTagSuggestionRequest(BaseModel):
    """Request to reject a tag suggestion."""

    node_id: str
    tag_name: str
    tag_value: str
    reason: str


# Fix forward references
Node.model_rebuild()
NodeWithRelations.model_rebuild()
