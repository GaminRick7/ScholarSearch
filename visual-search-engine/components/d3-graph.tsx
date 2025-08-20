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

    // Create responsive dimensions
    const containerWidth = svgRef.current.clientWidth || width
    const containerHeight = height

    // Set up the simulation
    const simulation = d3
      .forceSimulation(data.nodes)
      .force(
        "link",
        d3
          .forceLink(data.links)
          .id((d: any) => d.id)
          .strength(0.3),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .force("collision", d3.forceCollide().radius(30))

    // Create the SVG container
    const container = svg
      .attr("width", containerWidth)
      .attr("height", containerHeight)
      .attr("viewBox", `0 0 ${containerWidth} ${containerHeight}`)
      .style("background", "transparent")

    // Add zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform)
      })

    svg.call(zoom)

    const g = container.append("g")

    // Create arrow markers for directed edges
    const defs = g.append("defs")
    defs
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("orient", "auto")
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "hsl(var(--muted-foreground))")

    // Create links
    const link = g
      .append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "hsl(var(--border))")
      .attr("stroke-width", (d: any) => Math.sqrt(d.strength * 3))
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", "url(#arrowhead)")

    // Create node groups
    const nodeGroup = g
      .append("g")
      .selectAll("g")
      .data(data.nodes)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .style("cursor", "pointer")

    // Add circles for nodes
    const node = nodeGroup
      .append("circle")
      .attr("r", (d) => {
        if (d.type === "query") return 20
        if (d.type === "related") return 15
        if (d.type === "subtopic") return 12
        return 10
      })
      .attr("fill", (d) => {
        if (d.type === "query") return "hsl(var(--primary))"
        if (d.type === "related") return "hsl(var(--secondary))"
        if (d.type === "subtopic") return "hsl(var(--accent))"
        return "hsl(var(--muted-foreground))"
      })
      .attr("stroke", "hsl(var(--background))")
      .attr("stroke-width", 2)
      .style("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.1))")

    // Add labels
    const labels = nodeGroup
      .append("text")
      .text((d) => (d.id.length > 15 ? d.id.substring(0, 15) + "..." : d.id))
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-size", (d) => {
        if (d.type === "query") return "14px"
        if (d.type === "related") return "12px"
        return "10px"
      })
      .attr("font-weight", (d) => (d.type === "query" ? "bold" : "normal"))
      .attr("fill", "hsl(var(--foreground))")
      .style("pointer-events", "none")
      .style("user-select", "none")

    // Add connection count badges
    const badges = nodeGroup
      .append("circle")
      .attr("r", 8)
      .attr("cx", 15)
      .attr("cy", -15)
      .attr("fill", "hsl(var(--primary))")
      .attr("stroke", "hsl(var(--background))")
      .attr("stroke-width", 2)

    nodeGroup
      .append("text")
      .text((d) => d.connections)
      .attr("x", 15)
      .attr("y", -15)
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .attr("fill", "hsl(var(--primary-foreground))")
      .style("pointer-events", "none")

    // Add hover effects
    nodeGroup
      .on("mouseenter", function (event, d) {
        d3.select(this)
          .select("circle")
          .transition()
          .duration(200)
          .attr("r", (d: any) => {
            if (d.type === "query") return 24
            if (d.type === "related") return 18
            if (d.type === "subtopic") return 15
            return 12
          })
          .style("filter", "drop-shadow(0 4px 8px rgba(0,0,0,0.2))")
      })
      .on("mouseleave", function (event, d) {
        d3.select(this)
          .select("circle")
          .transition()
          .duration(200)
          .attr("r", (d: any) => {
            if (d.type === "query") return 20
            if (d.type === "related") return 15
            if (d.type === "subtopic") return 12
            return 10
          })
          .style("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.1))")
      })
      .on("click", (event, d) => {
        setSelectedNode(d)
        onNodeClick?.(d)
      })

    // Add drag behavior
    const drag = d3
      .drag<SVGGElement, Node>()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on("drag", (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })

    nodeGroup.call(drag)

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)

      nodeGroup.attr("transform", (d) => `translate(${d.x},${d.y})`)
    })

    // Cleanup function
    return () => {
      simulation.stop()
    }
  }, [data, width, height, onNodeClick])

  return (
    <div className="relative w-full">
      <svg ref={svgRef} className="w-full border rounded-lg bg-card" style={{ height: `${height}px` }} />

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
              <h3 className="font-semibold mb-2">{selectedNode.id}</h3>
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
export function generateGraphData(searchResults: any): GraphData {
  const nodes: Node[] = searchResults.nodes.map((node: any) => ({
    ...node,
    x: Math.random() * 400 + 200,
    y: Math.random() * 300 + 150,
  }))

  const links: Link[] = []
  const queryNode = nodes.find((n) => n.type === "query")

  if (queryNode) {
    // Connect query node to all other nodes
    nodes.forEach((node) => {
      if (node.id !== queryNode.id) {
        links.push({
          source: queryNode.id,
          target: node.id,
          strength: node.type === "related" ? 0.8 : 0.5,
        })
      }
    })

    // Add some connections between related nodes
    const relatedNodes = nodes.filter((n) => n.type === "related")
    for (let i = 0; i < relatedNodes.length - 1; i++) {
      if (Math.random() > 0.5) {
        links.push({
          source: relatedNodes[i].id,
          target: relatedNodes[i + 1].id,
          strength: 0.3,
        })
      }
    }

    // Connect subtopics to related topics
    const subtopicNodes = nodes.filter((n) => n.type === "subtopic")
    subtopicNodes.forEach((subtopic) => {
      const randomRelated = relatedNodes[Math.floor(Math.random() * relatedNodes.length)]
      if (randomRelated) {
        links.push({
          source: randomRelated.id,
          target: subtopic.id,
          strength: 0.4,
        })
      }
    })
  }

  return { nodes, links }
}
