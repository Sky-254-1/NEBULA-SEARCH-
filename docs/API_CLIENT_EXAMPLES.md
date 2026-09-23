# API Client Examples

This document provides code examples for integrating with Nebula Search API.

---

## Python

### Basic Search

```python
import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

async def search(query: str, backend: str = "wikipedia"):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        params = {"q": query, "backend": backend, "page": 1, "page_size": 10}
        
        response = await client.get(
            f"{BASE_URL}/api/v1/search/web",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
results = await search("Python programming language")
for result in results:
    print(f"{result['title']}: {result['url']}")
```

### AI Answers

```python
import httpx

async def ask_ai(prompt: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = await client.post(
            f"{BASE_URL}/api/v1/ai/ask",
            headers=headers,
            json={"prompt": prompt}
        )
        response.raise_for_status()
        return response.json()

# Usage
answer = await ask_ai("What is quantum computing?")
print(f"AI: {answer['answer']}")
```

### Document Upload

```python
import httpx

async def upload_document(file_path: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = await client.post(
                f"{BASE_URL}/api/v1/storage/documents",
                headers=headers,
                files=files
            )
            response.raise_for_status()
            return response.json()

# Usage
doc = await upload_document("report.pdf")
print(f"Uploaded: {doc['filename']}")
```

---

## JavaScript/TypeScript

### Using Axios

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
  },
});

// Search
export const search = async (
  query: string,
  backend: string = 'wikipedia',
  page: number = 1
) => {
  const response = await client.get('/api/v1/search/web', {
    params: { q: query, backend, page, page_size: 10 },
  });
  return response.data;
};

// AI Answer
export const askAI = async (prompt: string) => {
  const response = await client.post('/api/v1/ai/ask', { prompt });
  return response.data;
};

// Document Upload
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await client.post(
    '/api/v1/storage/documents',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );
  return response.data;
};
```

### Using fetch

```javascript
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

async function search(query, backend = 'wikipedia') {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/search/web?q=${encodeURIComponent(query)}&backend=${backend}`,
    {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
      },
    }
  );
  if (!response.ok) throw new Error('Search failed');
  return await response.json();
}

// Usage
search('Machine learning').then(results => {
  console.log(results);
});
```

---

## cURL

### Search

```bash
curl -X GET "http://localhost:8000/api/v1/search/web?q=python&backend=wikipedia&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### AI Answer

```bash
curl -X POST "http://localhost:8000/api/v1/ai/ask" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Docker?"}'
```

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/v1/storage/documents" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf"
```

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

---

## Command-Line Tool

### Python CLI

```python
#!/usr/bin/env python3
"""Command-line tool for Nebula Search API."""

import argparse
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    parser = argparse.ArgumentParser(description="Nebula Search CLI")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--backend", default="wikipedia", 
                       choices=["wikipedia", "brave", "serpapi"])
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    args = parser.parse_args()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/search/web",
            params={
                "q": args.query,
                "backend": args.backend,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
        
        results = response.json()
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['url']}")
            print(f"   {result['snippet'][:150]}...")
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

Usage:
```bash
python nebula-cli.py "machine learning" --backend brave --page-size 20
```

---

## Authentication

### Getting an API Key

```bash
# Login to get JWT token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

### Token Refresh

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

---

## Error Handling

### Common Errors

```python
import httpx
from httpx import HTTPStatusError, RequestError

async def safe_search(query: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/search/web",
                params={"q": query},
                headers={"Authorization": f"Bearer {API_KEY}"},
            )
            response.raise_for_status()
            return response.json()
    except HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 429:
            print("Rate limited. Wait and retry.")
    except RequestError as e:
        print(f"Request error: {e}")

# Usage
await safe_search("test query")
```

---

## Rate Limiting

### Check Rate Limit Status

```javascript
// Rate limit headers in response
// X-RateLimit-Limit: 60
// X-RateLimit-Remaining: 58
// X-RateLimit-Reset: 1625097600

const response = await fetch(`${API_BASE_URL}/api/v1/search/web?q=test`, {
  headers: { Authorization: `Bearer ${API_KEY}` },
});

const remaining = response.headers.get('X-RateLimit-Remaining');
const resetTime = response.headers.get('X-RateLimit-Reset');

console.log(`Rate limit remaining: ${remaining}`);
console.log(`Rate limit resets at: ${resetTime}`);
```

### Implement Backoff

```javascript
async function searchWithBackoff(query, maxRetries = 5) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/search/web?q=${encodeURIComponent(query)}`,
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );
      
      if (response.status === 429) {
        const resetTime = response.headers.get('X-RateLimit-Reset');
        const waitTime = (resetTime - Date.now() / 1000) * 1000;
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
      
      if (!response.ok) throw new Error('Search failed');
      
      return await response.json();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 2 ** i * 1000));
    }
  }
}
```

---

## Streaming (AI Answers)

### Python

```python
import httpx

async def stream_ai_answer(prompt: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        async with client.stream("POST", 
            f"{BASE_URL}/api/v1/ai/ask/stream",
            headers=headers,
            json={"prompt": prompt}
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    print(data, end="", flush=True)

# Usage
await stream_ai_answer("Explain quantum computing in simple terms")
```

### JavaScript

```javascript
async function* streamAIAnswer(prompt) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/ai/ask/stream`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    }
  );

  if (!response.ok) throw new Error('Stream failed');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const text = decoder.decode(value, { stream: true });
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") return;
        yield JSON.parse(data).chunk;
      }
    }
  }
}

// Usage
for await (const chunk of streamAIAnswer("Explain AI")) {
  process.stdout.write(chunk);
}
```

---

## Support

For API support:
- **Documentation:** http://localhost:8000/docs
- **Email:** api@nebula-search.example.com
- **Issues:** https://github.com/Sky-254-1/Nebula-search-engine-/issues

---

*Last updated: July 1, 2026*
