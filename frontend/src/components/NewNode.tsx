import { useState } from 'react'
import { useNavigate, Link } from 'react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { nodesApi, tagsApi } from '../api/client'
import type { NodeCreate } from '../types'

interface TagInput {
  name: string
  value: string
}

export default function NewNode() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [content, setContent] = useState('')
  const [source, setSource] = useState('')
  const [tags, setTags] = useState<TagInput[]>([])
  const [newTagName, setNewTagName] = useState('')
  const [newTagValue, setNewTagValue] = useState('')

  // Fetch tag suggestions
  const { data: suggestions } = useQuery({
    queryKey: ['tagSuggestions'],
    queryFn: () => tagsApi.getSuggestions(),
  })

  const createMutation = useMutation({
    mutationFn: (data: NodeCreate) => nodesApi.create(data),
    onSuccess: (node) => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })

      // Show notification about found links
      if (node.edges.length > 0) {
        toast.success(`Node created! Found ${node.edges.length} related node${node.edges.length > 1 ? 's' : ''}!`, {
          duration: 5000,
        })
      } else {
        toast.success('Node created!')
      }

      navigate(`/node/${node.id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create node')
    },
  })

  const handleAddTag = () => {
    if (newTagName.trim() && newTagValue.trim()) {
      setTags([...tags, { name: newTagName.trim(), value: newTagValue.trim() }])
      setNewTagName('')
      setNewTagValue('')
    }
  }

  const handleRemoveTag = (index: number) => {
    setTags(tags.filter((_, i) => i !== index))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!content.trim()) {
      toast.error('Content is required')
      return
    }

    if (!source.trim()) {
      toast.error('Source is required')
      return
    }

    createMutation.mutate({
      content: content.trim(),
      source: source.trim(),
      tags,
    })
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <Link to="/" className="theme-text-muted flex items-center space-x-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back</span>
        </Link>
        <h1 className="text-2xl font-bold theme-text-heading">New Node</h1>
        <div className="w-16"></div> {/* Spacer for centering */}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Source */}
        <div className="card">
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Source <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="input w-full px-3"
            placeholder="URL, filepath, person's name, etc."
            autoFocus
          />
          <p className="text-xs theme-text-muted mt-2">
            Where did this information come from?
          </p>
        </div>

        {/* Content */}
        <div className="card">
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Content <span className="text-red-500">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={8}
            className="input w-full px-3 resize-y"
            placeholder="Paste or type your intel snippet here...

Examples:
- IOCs from a threat report
- Notes from a conversation
- Snippet from a blog post
- List of suspicious domains"
          />
          <p className="text-xs theme-text-muted mt-2">
            IOCs (IPs, domains, hashes) and threat actors will be automatically extracted.
          </p>
        </div>

        {/* Tags */}
        <div className="card">
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Additional Tags
          </label>

          {/* Existing tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tags.map((tag, index) => (
                <span key={index} className="tag tag-custom flex items-center">
                  {tag.name}: {tag.value}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(index)}
                    className="ml-1 hover:text-purple-900 dark:hover:text-purple-300"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Add new tag */}
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="block text-xs theme-text-muted mb-1">Tag Name</label>
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className="input w-full px-3 text-sm"
                placeholder="e.g., campaign, adversary, tlp"
                list="tag-names"
              />
              <datalist id="tag-names">
                {suggestions?.names.map((name) => (
                  <option key={name} value={name} />
                ))}
              </datalist>
            </div>
            <div className="flex-1">
              <label className="block text-xs theme-text-muted mb-1">Tag Value</label>
              <input
                type="text"
                value={newTagValue}
                onChange={(e) => setNewTagValue(e.target.value)}
                className="input w-full px-3 text-sm"
                placeholder="e.g., Operation Cobalt, APT29"
                list="tag-values"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleAddTag()
                  }
                }}
              />
              <datalist id="tag-values">
                {suggestions?.values.map((value) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
            </div>
            <button
              type="button"
              onClick={handleAddTag}
              className="btn btn-secondary"
              disabled={!newTagName.trim() || !newTagValue.trim()}
            >
              Add
            </button>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-4">
          <Link to="/" className="btn btn-secondary">
            Cancel
          </Link>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Node'}
          </button>
        </div>
      </form>
    </div>
  )
}
