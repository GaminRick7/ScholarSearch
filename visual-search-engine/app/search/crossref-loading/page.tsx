"use client"

import {useEffect, useState} from "react";
import {useSearchParams} from "next/navigation";

export default function CrossrefLoading() {
    const searchParams = useSearchParams();
    const title = searchParams.get('title');
    const authors = searchParams.getAll('authors');
    const paper_id = searchParams.get('paper_id');
    const [error, setError] = useState("");

    useEffect(() => {
        async function fetchCrossRef() {
            try {
                // Call the smart paper access API
                const response = await fetch('http://localhost:8000/api/v1/papers/access', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: title,
                        authors: authors,
                        id: paper_id
                    })
                });


                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        // Open the URL in this tab
                        window.location.href = result.url;
                    }
                } else {
                    if (response.status === 400) {
                        setError("Please enter a valid query.")
                    } else {
                        const query = encodeURIComponent(`${title} ${authors.join(' ')}`);
                        window.location.href = `https://scholar.google.com/scholar?q=${query}`;
                    }
                }
            } catch (error) {
                console.error('Failed to access paper:', error);
                const query = encodeURIComponent(`${title} ${authors.join(' ')}`);
                window.location.href = `https://scholar.google.com/scholar?q=${query}`;
            }
        }

        fetchCrossRef();
    }, [title, authors, paper_id]);

    return (
        <div style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh"
        }}>
            {!error ? (
                <>
                    <p>Fetching your CrossRef link...</p>
                    <div
                        // Spinner animation
                        style={{
                            width: 40,
                            height: 40,
                            margin: '20px auto',
                            border: '4px solid #ccc',
                            borderTop: '4px solid #333',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                        }}
                    />
                    <style>{`
                    @keyframes spin {
                      0% { transform: rotate(0deg); }
                      100% { transform: rotate(360deg); }
                    }
                  `}</style>

                </>
            ) : (
                <p style={{color: "red"}}>{error}</p>
            )}
        </div>
    );
}
