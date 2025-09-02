"use client"

import type React from "react"
import {useState, useEffect} from "react"
import {Button} from "@/components/ui/button"
import {Card, CardContent} from "@/components/ui/card"
import {Badge} from "@/components/ui/badge"
import {Input} from "@/components/ui/input"
import {
    ArrowRight,
    Network,
    Zap,
    Eye,
    Github,
    Twitter,
    Mail,
    Moon,
    Sun,
    Search,
    BookOpen,
    Brain,
    TrendingUp
} from "lucide-react"
import {useTheme} from "next-themes"
import {ParticlesBackground} from "@/components/particles-background"
import {useRouter} from "next/navigation"
import Link from "next/link";
import {apiService} from "@/lib/api"

export default function HomePage() {
    const {theme, setTheme} = useTheme()
    const router = useRouter()
    const [mounted, setMounted] = useState(false)

    const useDebounce = (value: string, delay: number) => {
        const [debouncedValue, setDebouncedValue] = useState('');

        useEffect(() => {
            const handler = setTimeout(() => {
                setDebouncedValue(value);
            }, delay);

            return () => {
                // on new state, useEffect will clean up and clear this timeout, preventing the call if it doesnt happen within the delay
                clearTimeout(handler);
            };
        }, [value, delay]);

        return debouncedValue;
    }

    const [query, setQuery] = useState("")
    const debouncedQuery = useDebounce(query, 400);


    const [suggestions, setSuggestions] = useState<string[]>([])
    const [showSuggestions, setShowSuggestions] = useState<boolean>(false)
    const [isSearchFocused, setIsSearchFocused] = useState<boolean>(false);


    useEffect(() => {
        setMounted(true)
    }, [])

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (debouncedQuery.trim().length > 2) {
                try {
                    const suggestionTexts = await apiService.getSuggestions(debouncedQuery);
                    setSuggestions(suggestionTexts);
                    setShowSuggestions(true);
                } catch (err) {
                    console.error('Failed to get suggestions:', err);
                    setSuggestions([]);
                    setShowSuggestions(false);
                }
            } else {
                setSuggestions([]);
                setShowSuggestions(false);
            }
        };

        fetchSuggestions();
    }, [debouncedQuery]); // fires on query change


    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return

        // Redirect to search page with query parameter
        router.push(`/search?q=${encodeURIComponent(query)}`)
    }

    const handleQueryChange = async (value: string) => {
        setQuery(value)
    }

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion)
        setShowSuggestions(false)
        router.push(`/search?q=${encodeURIComponent(suggestion)}`)
    }

    const handleNewSearch = () => {
        setQuery("")
    }

    return (
        <div className="min-h-screen bg-background relative">
            <ParticlesBackground/>

            <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <Link href="/" className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                <Network className="w-5 h-5 text-primary-foreground"/>
                            </div>
                            <span className="font-bold text-xl">ScholarSearch</span>
                        </Link>
                        <div className="flex items-center space-x-4">
                            {mounted && (
                                <Button variant="ghost" size="sm"
                                        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
                                    {theme === "dark" ? <Sun className="w-4 h-4"/> : <Moon className="w-4 h-4"/>}
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            <section
                className="min-h-screen pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative z-10 flex items-center justify-center">
                <div className="max-w-7xl mx-auto text-center my-auto">
                    <Badge variant="secondary" className="mb-6">
                        <Zap className="w-3 h-3 mr-1"/>
                        Powered by AI & Hybrid Search
                    </Badge>

                    <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
                        <span className="text-primary">ScholarSearch</span> 2.0
                    </h1>

                    <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
                        Discover research papers with intelligent hybrid search combining traditional text matching and
                        AI-powered semantic understanding.
                    </p>

                    <div className="max-w-2xl mx-auto mb-12">
                        <form onSubmit={handleSearch} className="relative"
                              onFocus={() => setIsSearchFocused(true)}
                              onBlur={() => setIsSearchFocused(false)}
                        >
                            <div className="relative">
                                <Search
                                    className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground"/>
                                <Input
                                    type="text"
                                    placeholder="Search for research papers, authors, or topics..."
                                    value={query}
                                    onChange={(e) => handleQueryChange(e.target.value)}
                                    className="pl-12 pr-24 h-14 text-lg rounded-full border-2 focus:border-primary transition-colors"
                                />
                                <Button
                                    type="submit"
                                    size="sm"
                                    className="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-full px-6 pulse-glow"
                                    disabled={!query.trim()}
                                >
                                    Search
                                </Button>
                            </div>

                            {/* Search Suggestions */}
                            {showSuggestions && suggestions.length > 0 && isSearchFocused && (
                                <div
                                    className="absolute top-full left-0 right-0 mt-2 bg-background border border-border rounded-lg shadow-lg z-50">
                                    {suggestions.map((suggestion, index) => (
                                        <button
                                            key={index}
                                            onMouseDown={() => handleSuggestionClick(suggestion)}
                                            className="w-full text-left px-4 py-3 hover:cursor-pointer hover:bg-muted dark:hover:bg-gray-800 transition-colors first:rounded-t-lg last:rounded-b-lg"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </form>

                        <div className="mt-6">
                            <p className="text-sm text-muted-foreground mb-3">Try searching for:</p>
                            <div className="flex flex-wrap gap-2 justify-center">
                                {["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision"].map(
                                    (suggestion) => (
                                        <Button
                                            key={suggestion}
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setQuery(suggestion)}
                                            className="rounded-full"
                                        >
                                            {suggestion}
                                        </Button>
                                    ),
                                )}
                            </div>
                        </div>
                    </div>


                </div>
            </section>

            <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30 relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl sm:text-4xl font-bold mb-4">Why Choose ScholarNet 2.0?</h2>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            Advanced research paper discovery powered by cutting-edge AI and hybrid search technology.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
                            <CardContent className="p-8 text-center">
                                <div
                                    className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <Brain className="w-8 h-8 text-primary"/>
                                </div>
                                <h3 className="text-xl font-semibold mb-4">AI-Powered Search</h3>
                                <p className="text-muted-foreground leading-relaxed">
                                    BERT embeddings understand context and meaning, not just keywords. Find conceptually
                                    related research.
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
                            <CardContent className="p-8 text-center">
                                <div
                                    className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <BookOpen className="w-8 h-8 text-secondary"/>
                                </div>
                                <h3 className="text-xl font-semibold mb-4">Comprehensive Coverage</h3>
                                <p className="text-muted-foreground leading-relaxed">
                                    Access millions of research papers across all disciplines with advanced filtering
                                    and ranking.
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
                            <CardContent className="p-8 text-center">
                                <div
                                    className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <TrendingUp className="w-8 h-8 text-accent"/>
                                </div>
                                <h3 className="text-xl font-semibold mb-4">Performance Optimized</h3>
                                <p className="text-muted-foreground leading-relaxed">
                                    Sub-200ms search response times with intelligent caching and optimized search
                                    algorithms.
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </section>

            <section className="py-20 px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl sm:text-4xl font-bold mb-4">How It Works</h2>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            Three simple steps to unlock the power of intelligent research discovery.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-12">
                        <div className="text-center">
                            <div
                                className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-6 text-2xl font-bold text-primary-foreground">
                                1
                            </div>
                            <h3 className="text-xl font-semibold mb-4">Enter Your Query</h3>
                            <p className="text-muted-foreground leading-relaxed">
                                Type in any research topic, paper title, author name, or concept you want to explore.
                            </p>
                        </div>

                        <div className="text-center">
                            <div
                                className="w-20 h-20 bg-secondary rounded-full flex items-center justify-center mx-auto mb-6 text-2xl font-bold text-secondary-foreground">
                                2
                            </div>
                            <h3 className="text-xl font-semibold mb-4">AI Analysis</h3>
                            <p className="text-muted-foreground leading-relaxed">
                                Our hybrid search combines BM25 text matching with BERT semantic understanding for
                                comprehensive results.
                            </p>
                        </div>

                        <div className="text-center">
                            <div
                                className="w-20 h-20 bg-accent rounded-full flex items-center justify-center mx-auto mb-6 text-2xl font-bold text-accent-foreground">
                                3
                            </div>
                            <h3 className="text-xl font-semibold mb-4">Discover & Explore</h3>
                            <p className="text-muted-foreground leading-relaxed">
                                Browse relevant papers with detailed metadata, citations, and direct DOI links to full
                                papers.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="py-20 px-4 sm:px-6 lg:px-8 bg-primary/5 relative z-10">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-3xl sm:text-4xl font-bold mb-6">Ready to Transform Your Research?</h2>
                    <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                        Join researchers worldwide who have already discovered the power of intelligent paper discovery.
                    </p>
                    <Button size="lg" onClick={() => document.querySelector("input")?.focus()}
                            className="text-lg px-8 py-6">
                        Start Searching Now
                        <ArrowRight className="ml-2 w-5 h-5"/>
                    </Button>
                </div>
            </section>

            <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-border relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row justify-between items-center">
                        <div className="flex items-center space-x-2 mb-4 md:mb-0">
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                <Network className="w-5 h-5 text-primary-foreground"/>
                            </div>
                            <span className="font-bold text-xl">ScholarNet 2.0</span>
                        </div>

                        <div className="flex items-center space-x-6">
                            <Button variant="ghost" size="sm" asChild>
                                <a href="https://github.com/GaminRick7/ScholarSearch" target="_blank" rel="noopener noreferrer">
                                    <Github className="w-4 h-4 mr-2"/>
                                    GitHub
                                </a>
                            </Button>
                            <Button variant="ghost" size="sm">
                                <Twitter className="w-4 h-4 mr-2"/>
                                Twitter
                            </Button>
                            <Button variant="ghost" size="sm">
                                <Mail className="w-4 h-4 mr-2"/>
                                Contact
                            </Button>
                        </div>
                    </div>

                    <div className="mt-8 pt-8 border-t border-border text-center text-muted-foreground">
                        <p>&copy; 2024 ScholarNet 2.0. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
