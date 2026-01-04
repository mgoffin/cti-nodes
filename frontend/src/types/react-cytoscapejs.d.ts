declare module 'react-cytoscapejs' {
  import { Component } from 'react'
  import type { Core, ElementDefinition, Stylesheet, LayoutOptions } from 'cytoscape'

  interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    stylesheet?: Stylesheet[]
    style?: React.CSSProperties
    cy?: (cy: Core) => void
    layout?: LayoutOptions
    className?: string
    id?: string
    zoom?: number
    pan?: { x: number; y: number }
    minZoom?: number
    maxZoom?: number
    zoomingEnabled?: boolean
    userZoomingEnabled?: boolean
    panningEnabled?: boolean
    userPanningEnabled?: boolean
    boxSelectionEnabled?: boolean
    autoungrabify?: boolean
    autounselectify?: boolean
    autolock?: boolean
    [key: string]: unknown
  }

  export default class CytoscapeComponent extends Component<CytoscapeComponentProps> {}
}
