"use client"

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { X, Info } from "lucide-react"

interface Node {
  id: string
  type: string
  connections: number
  title?: string
  abstract?: string
  authors?: string
  venue?: string
  year?: number
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface Link {
  source: string | Node
  target: string | Node
  strength: number
}

interface GraphData {
  nodes: Node[]
  links: Link[]
}

interface D3GraphProps {
  data: GraphData
  width?: number
  height?: number
  onNodeClick?: (node: Node) => void
}

export function D3Graph({ data, width = 800, height = 600, onNodeClick }: D3GraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    // Specify the dimensions of the chart
    const chartWidth = 928
    const chartHeight = 680

    // Specify the color scale
    const color = d3.scaleOrdinal(d3.schemeCategory10)

    // The force simulation mutates links and nodes, so create a copy
    // so that re-evaluating this cell produces the same result
    const links = data.links.map(d => ({...d}))
    const nodes = data.nodes.map(d => ({...d}))

    // Create a simulation with several forces
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id))
      .force("charge", d3.forceManyBody().strength((d: any) => -(d.connections)))
      .force("x", d3.forceX())
      .force("y", d3.forceY())

    // Create the SVG container
    const container = svg
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .attr("viewBox", [-chartWidth / 2, -chartHeight / 2, chartWidth, chartHeight])
      .style("max-width", "100%")
      .style("height", "auto")

    // Add a line for each link
    const link = container.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d: any) => Math.sqrt((d.strength || 1) * 3))

    // Add a circle for each node
    const node = container.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d: any) => {
        // Scale circle size based on citation count
        const baseRadius = 5
        const citationMultiplier = Math.min(d.connections || 0, 100) / 100
        return baseRadius + (citationMultiplier * 8) // Range: 5 to 13
      })
      .attr("fill", (d: any) => {
        if (d.type === "Citation Result") return "orange"
        return color(d.type || "paper")
      })
      .style("cursor", "pointer")

    // Add title tooltip
    node.append("title")
      .text((d: any) => d.title || d.id)

    // Add citation count text in the center
    const nodeText = container.append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-size", "8px")
      .attr("font-weight", "bold")
      .attr("fill", "white")
      .style("pointer-events", "none")
      .text((d: any) => d.connections)

    // Add hover effects
    node
      .on("mouseenter", function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d: any) => {
            const baseRadius = 5
            const citationMultiplier = Math.min(d.connections || 0, 100) / 100
            const normalSize = baseRadius + (citationMultiplier * 8)
            return normalSize * 1.3 // 30% larger on hover
          })
          .style("filter", "drop-shadow(0 4px 8px rgba(0,0,0,0.2))")
      })
      .on("mouseleave", function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d: any) => {
            const baseRadius = 5
            const citationMultiplier = Math.min(d.connections || 0, 100) / 100
            return baseRadius + (citationMultiplier * 8)
          })
          .style("filter", "none")
      })
      .on("click", (event, d) => {
        setSelectedNode(d)
        onNodeClick?.(d)
      })

    // Add a drag behavior
    node.call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended))

    // Set the position attributes of links and nodes each time the simulation ticks
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y)

      nodeText
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y)
    })

    // Reheat the simulation when drag starts, and fix the subject position
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    // Update the subject (dragged node) position during drag
    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    // Restore the target alpha so the simulation cools after dragging ends
    // Unfix the subject position now that it's no longer being dragged
    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    // Cleanup function
    return () => {
      simulation.stop()
    }
  }, [data, width, height, onNodeClick])

  return (
    <div className="relative w-full">
      <svg ref={svgRef} className="w-full h-full border rounded-lg bg-card" style={{ height: `${height}px` }} />

      {/* Node Details Modal */}
      {selectedNode && (
        <div className="absolute top-4 right-4 z-10">
          <Card className="w-80 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <Badge variant={selectedNode.type === "query" ? "default" : "secondary"}>{selectedNode.type}</Badge>
                <Button variant="ghost" size="sm" onClick={() => setSelectedNode(null)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <h3 className="font-semibold mb-2">{selectedNode.title || selectedNode.id}</h3>
              
              {/* Paper metadata */}
              <div className="flex flex-wrap gap-2 mb-3">
                {selectedNode.authors && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span className="font-medium">Authors:</span>
                    <span>
                      {(() => {
                        const authors = String(selectedNode.authors);
                        const authorList = authors.split(',').map(a => a.trim());
                        if (authorList.length <= 2) {
                          return authorList.join(', ');
                        } else {
                          return `${authorList.slice(0, 2).join(', ')} +${authorList.length - 2} more`;
                        }
                      })()}
                    </span>
                  </div>
                )}
                {selectedNode.venue && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span className="font-medium">Venue:</span>
                    <span>{selectedNode.venue}</span>
                  </div>
                )}
                {selectedNode.year && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span className="font-medium">Year:</span>
                    <span>{selectedNode.year}</span>
                  </div>
                )}
              </div>
              
              {selectedNode.abstract && (
                <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
                  {selectedNode.abstract}
                </p>
              )}
              
              <p className="text-sm text-muted-foreground mb-3">{selectedNode.connections} connections in the graph</p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Info className="w-3 h-3" />
                Click and drag to move nodes around
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// Helper function to generate graph data from search results
export function generateGraphData(searchResults: any[]): GraphData {
  if (!searchResults || searchResults.length === 0) {
    return { nodes: [], links: [] }
  }

  // Convert search results to nodes
  const nodes: Node[] = searchResults.map((paper, index) => ({
    id: paper.id || `paper_${index}`,
    type: "Top Result",
    connections: paper.citations || paper.reference_count || Math.floor(Math.random() * 100) + 10,
    title: paper.title || paper.name || `Paper ${index + 1}`,
    abstract: paper.abstract || paper.summary || paper.description || undefined,
    authors: paper.authors || paper.author || paper.creator || undefined,
    venue: paper.venue || paper.journal || paper.conference || "Unknown",
    year: paper.year || paper.publication_year || 2023,
    x: 0, // Will be set by D3 force simulation
    y: 0
  }))

  // Create citation papers for each result
  const citationNodes: Node[] = []
  const citationLinks: Link[] = []
  
  nodes.forEach((resultNode, index) => {
    // Generate 3 citation papers for each result
    for (let i = 0; i < 3; i++) {
      const citationId = `citation_${resultNode.id}_${i}`
      const citationNode: Node = {
        id: citationId,
        type: "Citation Result",
        connections: Math.floor(Math.random() * 200) + 50, // Random citation count 50-250
        title: `${resultNode.title|| resultNode.id}`,
        abstract: resultNode.abstract || `Related work on ${resultNode.title?.substring(0, 50) || resultNode.id}`,
        authors: `Author ${i + 1}, Author ${i + 2}`,
        venue: `Journal ${i + 1}`,
        year: (resultNode.year || 2023) + Math.floor(Math.random() * 3) - 1, // ±1 year from cited paper
        x: 0,
        y: 0
      }
      citationNodes.push(citationNode)
      
      // Create link from citation paper TO the result paper (citation relationship)
      citationLinks.push({
        source: citationId,
        target: resultNode.id,
        strength: 0.8
      })
    }
  })
  
  // Combine all nodes and links
  const allNodes = [...nodes, ...citationNodes]
  const allLinks = citationLinks
  
  // Create some additional connections between citation papers for variety
  for (let i = 0; i < citationNodes.length - 1; i++) {
    if (Math.random() > 0.7) { // 30% chance of connection
      allLinks.push({
        source: citationNodes[i].id,
        target: citationNodes[i + 1].id,
        strength: Math.random() * 0.3 + 0.2
      })
    }
  }

  console.log(`Generated graph with ${allNodes.length} nodes and ${allLinks.length} links`)
  console.log('Sample node:', allNodes[0])
  console.log('Sample link:', allLinks[0])

  return { nodes: allNodes, links: allLinks }
}
