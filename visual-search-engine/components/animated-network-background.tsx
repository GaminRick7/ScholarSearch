"use client"

import { useEffect, useRef } from "react"

interface Node {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  opacity: number
}

interface Connection {
  from: number
  to: number
  opacity: number
}

export function AnimatedNetworkBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const nodesRef = useRef<Node[]>([])
  const connectionsRef = useRef<Connection[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    const initializeNodes = () => {
      const nodeCount = Math.floor((canvas.width * canvas.height) / 50000) // Responsive node count
      nodesRef.current = []
      connectionsRef.current = []

      for (let i = 0; i < nodeCount; i++) {
        nodesRef.current.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          radius: Math.random() * 2 + 1,
          opacity: Math.random() * 0.3 + 0.1,
        })
      }

      // Create connections between nearby nodes
      for (let i = 0; i < nodesRef.current.length; i++) {
        for (let j = i + 1; j < nodesRef.current.length; j++) {
          const dx = nodesRef.current[i].x - nodesRef.current[j].x
          const dy = nodesRef.current[i].y - nodesRef.current[j].y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < 150 && Math.random() < 0.3) {
            connectionsRef.current.push({
              from: i,
              to: j,
              opacity: Math.random() * 0.2 + 0.05,
            })
          }
        }
      }
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Update and draw connections
      ctx.strokeStyle = `rgba(99, 102, 241, 0.1)` // Primary color with low opacity
      ctx.lineWidth = 1

      connectionsRef.current.forEach((connection) => {
        const fromNode = nodesRef.current[connection.from]
        const toNode = nodesRef.current[connection.to]

        if (fromNode && toNode) {
          ctx.globalAlpha = connection.opacity
          ctx.beginPath()
          ctx.moveTo(fromNode.x, fromNode.y)
          ctx.lineTo(toNode.x, toNode.y)
          ctx.stroke()
        }
      })

      // Update and draw nodes
      nodesRef.current.forEach((node) => {
        // Update position
        node.x += node.vx
        node.y += node.vy

        // Bounce off edges
        if (node.x <= 0 || node.x >= canvas.width) node.vx *= -1
        if (node.y <= 0 || node.y >= canvas.height) node.vy *= -1

        // Keep nodes in bounds
        node.x = Math.max(0, Math.min(canvas.width, node.x))
        node.y = Math.max(0, Math.min(canvas.height, node.y))

        // Pulse opacity
        node.opacity += (Math.random() - 0.5) * 0.01
        node.opacity = Math.max(0.05, Math.min(0.4, node.opacity))

        // Draw node
        ctx.globalAlpha = node.opacity
        ctx.fillStyle = `rgb(99, 102, 241)` // Primary color
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
        ctx.fill()
      })

      ctx.globalAlpha = 1
      animationRef.current = requestAnimationFrame(animate)
    }

    resizeCanvas()
    initializeNodes()
    animate()

    const handleResize = () => {
      resizeCanvas()
      initializeNodes()
    }

    window.addEventListener("resize", handleResize)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      window.removeEventListener("resize", handleResize)
    }
  }, [])

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0" style={{ opacity: 0.6 }} />
}
