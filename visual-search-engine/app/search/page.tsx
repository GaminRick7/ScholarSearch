"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Network, Search, Loader2, Moon, Sun, ExternalLink, Calendar, Users, TrendingUp } from "lucide-react"
import { useTheme } from "next-themes"
import { D3Graph, generateGraphData } from "@/components/d3-graph"
import { ParticlesBackground } from "@/components/particles-background"
import { apiService, SearchResult, SearchResponse } from "@/lib/api"

export default function SearchPage() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const searchParams = useSearchParams()
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    setMounted(true)
    const q = searchParams.get("q")
    if (q) {
      setQuery(q)
      performSearch(q)
    }
  }, [searchParams])

  const performSearch = async (searchQuery: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const results = await apiService.searchPapers({
        query: searchQuery,
        page: 1,
        size: 20
      })
      
      setSearchResults(results)
    } catch (err) {
      console.error('Search failed:', err)
      setError('Search failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    // Update URL with new query
    router.push(`/search?q=${encodeURIComponent(query)}`)
    await performSearch(query)
  }

  const handleQueryChange = async (value: string) => {
    setQuery(value)
    
    if (value.trim().length > 2) {
      try {
        const suggestionsResponse = await apiService.getSuggestions(value)
        const suggestionTexts = suggestionsResponse.suggestions.map(s => s.text)
        setSuggestions(suggestionTexts)
        setShowSuggestions(true)
      } catch (err) {
        console.error('Failed to get suggestions:', err)
      }
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    router.push(`/search?q=${encodeURIComponent(suggestion)}`)
    performSearch(suggestion)
  }

  const handleNodeClick = (node: any) => {
    console.log("Node clicked:", node)
    // Here you could trigger a new search or show more details
  }

  const formatAuthors = (authors: string[]) => {
    if (authors.length <= 2) return authors.join(', ')
    return `${authors[0]}, ${authors[1]} +${authors.length - 2} more`
  }

  const formatAbstract = (abstract: string) => {
    if (abstract.length <= 150) return abstract
    return abstract.substring(0, 150) + '...'
  }

  return (
    <div className="min-h-screen bg-background relative">
      <ParticlesBackground />

      <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Network className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="font-bold text-xl">ScholarNet 2.0</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {mounted && (
                <Button variant="ghost" size="sm" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
                  {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </Button>
              )}
              <Button variant="outline" size="sm">
                Sign In
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="pt-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto relative">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search for research papers..."
                  value={query}
                  onChange={(e) => handleQueryChange(e.target.value)}
                  className="pl-12 pr-24 h-14 text-lg rounded-full border-2 focus:border-primary transition-colors"
                  disabled={isLoading}
                />
                <Button
                  type="submit"
                  size="sm"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-full px-6"
                  disabled={isLoading || !query.trim()}
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
                </Button>
              </div>
              
              {/* Search Suggestions */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-background border border-border rounded-lg shadow-lg z-50">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left px-4 py-3 hover:bg-muted transition-colors first:rounded-t-lg last:rounded-b-lg"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </form>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-destructive text-center">{error}</p>
            </div>
          )}

          {isLoading && (
            <div className="py-20 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-6">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Searching ScholarNet 2.0</h3>
              <p className="text-muted-foreground">Finding relevant research papers...</p>
            </div>
          )}

          {searchResults && !isLoading && (
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold mb-2">Search Results for "{searchResults.query}"</h2>
                <p className="text-muted-foreground">
                  Found {searchResults.total_results} papers in {searchResults.search_time_ms.toFixed(0)}ms
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Search type: {searchResults.search_type} • Page {searchResults.page} of {Math.ceil(searchResults.total_results / searchResults.size)}
                </p>
              </div>

              {/* Results Grid */}
              <div className="grid gap-6">
                {searchResults.results.map((paper, index) => (
                  <Card key={paper.paper_id} className="hover:shadow-lg transition-shadow duration-200">
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            Score: {paper.score.toFixed(2)}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {paper.search_type}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <div className="flex items-center space-x-1">
                            <Calendar className="w-4 h-4" />
                            <span>{paper.year}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Users className="w-4 h-4" />
                            <span>{paper.authors.length}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <TrendingUp className="w-4 h-4" />
                            <span>{paper.n_citation.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                      
                      <h3 className="text-xl font-semibold mb-2 text-primary hover:text-primary/80 transition-colors">
                        {paper.title}
                      </h3>
                      
                      <p className="text-muted-foreground mb-3">
                        <span className="font-medium">Authors:</span> {formatAuthors(paper.authors)}
                      </p>
                      
                      <p className="text-muted-foreground mb-3">
                        <span className="font-medium">Venue:</span> {paper.venue}
                      </p>
                      
                      <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                        {formatAbstract(paper.abstract)}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {paper.doi && (
                            <Button variant="outline" size="sm" asChild>
                              <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="w-4 h-4 mr-2" />
                                DOI
                              </a>
                            </Button>
                          )}
                        </div>
                        
                        <Button variant="ghost" size="sm">
                          View Details
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Pagination */}
              {searchResults.total_results > searchResults.size && (
                <div className="flex justify-center mt-8">
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      disabled={searchResults.page <= 1}
                      onClick={() => {
                        // Handle previous page
                      }}
                    >
                      Previous
                    </Button>
                    
                    <span className="px-4 py-2 text-sm text-muted-foreground">
                      Page {searchResults.page} of {Math.ceil(searchResults.total_results / searchResults.size)}
                    </span>
                    
                    <Button
                      variant="outline"
                      disabled={searchResults.page >= Math.ceil(searchResults.total_results / searchResults.size)}
                      onClick={() => {
                        // Handle next page
                      }}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
