"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ArrowLeft, Network, Search, Loader2, Moon, Sun, ExternalLink, Calendar, Users, TrendingUp, List, Network as NetworkIcon, Filter } from "lucide-react"
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
  const [viewMode, setViewMode] = useState<'list' | 'graph'>('list')
  const [citationWeight, setCitationWeight] = useState(0.5)
  const [isFiltersOpen, setIsFiltersOpen] = useState(false)

  useEffect(() => {
    setMounted(true)
    const q = searchParams.get("q")
    if (q) {
      setQuery(q)
      performSearch(q)
    }
  }, [searchParams])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFiltersOpen) {
        setIsFiltersOpen(false)
      }
      if (e.key === 'f' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        setIsFiltersOpen(true)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isFiltersOpen])

  const performSearch = async (searchQuery: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const results = await apiService.searchPapers({
        query: searchQuery,
        page: 1,
        size: 20,
        citation_weight: citationWeight
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
    
    // Close filters modal after search
    setIsFiltersOpen(false)
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

  const handleApplyFilters = async () => {
    if (query.trim()) {
      await performSearch(query)
    }
  }

  const handleResetFilters = () => {
    setCitationWeight(0.5)
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

          {/* View Toggle and Filters */}
          {searchResults && !isLoading && (
            <div className="mb-6 flex justify-between items-center">
              {/* View Toggle */}
              <div className="flex items-center space-x-2 bg-muted rounded-lg p-1">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="flex items-center space-x-2"
                >
                  <List className="w-4 h-4" />
                  <span>List View</span>
                </Button>
                <Button
                  variant={viewMode === 'graph' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('graph')}
                  className="flex items-center space-x-2"
                >
                  <NetworkIcon className="w-4 h-4" />
                  <span>Graph View</span>
                </Button>
              </div>
              
              {/* Filters Button - Only show in List View */}
              {viewMode === 'list' && (
                <Dialog open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="flex items-center space-x-2">
                      <Filter className="w-4 h-4" />
                      <span>Filters</span>
                      {citationWeight !== 0.5 && (
                        <Badge variant="secondary" className="ml-1 text-xs">
                          {citationWeight >= 1.0 ? 'Citation Only' : citationWeight > 0.5 ? 'Impact' : 'Relevance'}
                        </Badge>
                      )}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle>Search Filters & Options</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-6 py-4">
                      {/* Citation Weight Section */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-medium">Citation Weight</label>
                          <span className="text-sm text-muted-foreground">{citationWeight.toFixed(1)}</span>
                        </div>
                        <Slider
                          value={[citationWeight]}
                          onValueChange={(value) => setCitationWeight(value[0])}
                          max={1.0}
                          min={0.0}
                          step={0.1}
                          className="w-full"
                        />
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Relevance Focus</span>
                          <span>Impact Focus</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Higher values prioritize highly cited papers in search results
                        </p>
                        
                        {/* Current Setting Indicator */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="text-xs font-medium mb-1">Current Setting:</div>
                          <div className="text-xs text-muted-foreground">
                            {citationWeight === 0.5 ? (
                              "Default: Balanced approach between relevance and impact"
                            ) : citationWeight >= 1.0 ? (
                              "Citation-Only Sorting: Results ranked purely by citation count"
                            ) : citationWeight > 0.5 ? (
                              `Impact-focused: Papers with ${citationWeight.toFixed(1)}x citation boost`
                            ) : (
                              `Relevance-focused: Minimal citation influence (${citationWeight.toFixed(1)}x)`
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Divider */}
                      <div className="border-t border-border" />
                      
                      {/* Keyboard Shortcuts */}
                      <div className="p-3 bg-muted/30 rounded-lg border border-dashed border-border">
                        <div className="text-xs font-medium mb-2">Keyboard Shortcuts:</div>
                        <div className="text-xs text-muted-foreground space-y-1">
                          <div>• <kbd className="px-1 py-0.5 bg-background border rounded text-xs font-mono">Ctrl/Cmd + F</kbd> Open filters</div>
                          <div>• <kbd className="px-1 py-0.5 bg-background border rounded text-xs font-mono">Esc</kbd> Close filters</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex justify-between pt-4 border-t border-border">
                      <Button variant="ghost" onClick={handleResetFilters} size="sm">
                        Reset to Defaults
                      </Button>
                      <div className="flex space-x-2">
                        <Button variant="outline" onClick={() => setIsFiltersOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleApplyFilters} disabled={!query.trim()}>
                          Apply Filters
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          )}

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
                {citationWeight !== 0.5 && (
                  <div className="mt-2 flex items-center space-x-2">
                    <Badge variant="outline" className="text-xs">
                      <Filter className="w-3 h-3 mr-1" />
                      Citation Weight: {citationWeight.toFixed(1)}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {citationWeight >= 1.0 ? 'Citation-only sorting' : citationWeight > 0.5 ? 'Prioritizing impact' : 'Prioritizing relevance'}
                    </span>
                  </div>
                )}
              </div>

              {/* Conditional View Rendering */}
              {viewMode === 'list' ? (
                /* List View */
                <div className="grid gap-6">
                  {searchResults.results.map((paper, index) => (
                    <Card key={paper.paper_id} className="hover:shadow-lg transition-shadow duration-200">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center space-x-2">
                            {index === 0 && (
                              <Badge variant="default" className="bg-primary text-primary-foreground text-xs font-medium">
                                Top Result
                              </Badge>
                            )}
                            {/* Tags removed for cleaner list view */}
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
                        
                        <p className="text-muted-foreground mb-2">
                          <span className="font-medium">Authors:</span> {formatAuthors(paper.authors)}
                        </p>
                        
                        <p className="text-muted-foreground mb-2">
                          <span className="font-medium">Venue:</span> {paper.venue}
                        </p>
                        
                        <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
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
              ) : (
                /* Graph View */
                <div className="h-full border rounded-lg bg-muted/20">
                  <D3Graph
                    data={generateGraphData(searchResults.results)}
                    onNodeClick={handleNodeClick}
                  />
                </div>
              )}

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
