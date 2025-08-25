// API service for communicating with ScholarNet 2.0 backend

import {useEffect, useState} from "react";

const API_BASE_URL = 'http://localhost:8000';

export interface SearchRequest {
    query: string;
    page?: number;
    size?: number;
    filters?: Record<string, any>;
    bert_weight?: number;
    citation_weight?: number;
}

export interface SearchResult {
    paper_id: string;
    title: string;
    abstract: string;
    authors: string[];
    venue: string;
    year: number;
    n_citation: number;
    doi?: string;
    score: number;
    search_type: string;
    citation_boost?: number;
    citation_normalized?: number;
    bm25_score?: number;
    bert_score?: number;
}

export interface SearchResponse {
    query: string;
    total_results: number;
    page: number;
    size: number;
    results: SearchResult[];
    search_time_ms: number;
    search_type: string;
}

export interface Suggestion {
    type: 'paper' | 'author' | 'venue';
    text: string;
    paper_id?: string;
}

export interface SuggestionsResponse {
    suggestions: String[];
}

export interface Paper {
    paper_id: string;
    title: string;
    abstract: string;
    authors: string[];
    venue: string;
    year: number;
    n_citation: number;
    doi?: string;
    score: number;
    search_type: string;
}

export interface HealthResponse {
    status: string;
    timestamp: string;
    version: string;
    services: Record<string, string>;
}

export interface StatsResponse {
    total_papers: number;
    total_authors: number;
    total_venues: number;
    year_range: {
        min: number;
        max: number;
    };
    citation_stats: {
        total: number;
        average: number;
    };
}

class ApiService {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const config: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Search for papers
    async searchPapers(request: SearchRequest): Promise<SearchResponse> {
        return this.request<SearchResponse>('/api/v1/search', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Get paper by ID
    async getPaper(paperId: string): Promise<Paper> {
        return this.request<Paper>(`/api/v1/papers/${paperId}`);
    }

    // Get search suggestions
    async getSuggestions(query: string): Promise<string[]> {
        return this.request<string[]>(`/api/v1/suggest/${encodeURIComponent(query)}`);
    }

    // Get system statistics
    async getStats(): Promise<StatsResponse> {
        return this.request<StatsResponse>('/api/v1/stats');
    }

    // Health check
    async healthCheck(): Promise<HealthResponse> {
        return this.request<HealthResponse>('/health');
    }

    // Test API connection
    async testConnection(): Promise<boolean> {
        try {
            await this.healthCheck();
            return true;
        } catch {
            return false;
        }
    }
}

// Export singleton instance
export const apiService = new ApiService();

// Export the class for testing or custom instances
export {ApiService};
