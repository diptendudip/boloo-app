# RAG API Reference

Complete API documentation for the RAG (Retrieval Augmented Generation) implementation.

---

## Base URL

```
http://localhost:8000/v1/knowledge
```

---

## Authentication

All endpoints require authentication using JWT Bearer token.

```http
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. Semantic Search

Search for historically similar cases using natural language queries.

```http
POST /v1/knowledge/search
```

#### Request

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>`

**Body:**
```json
{
  "query": "string",                  // Required: Search query (Hindi/English)
  "top_k": 5,                        // Optional: Number of results (1-20), default: 5
  "similarity_threshold": 0.0         // Optional: Min similarity (0.0-1.0), default: 0.0
}
```

#### Response

**Status:** 200 OK

```json
{
  "query": "पानी की समस्या है गाँव में",
  "results": [
    {
      "similarity_score": 0.92,               // Similarity score (0-1)
      "description": "ग्राम-पटेलपारा...",     // Problem description
      "tag": "WATER_PROBLEM",                 // Problem category
      "district": "Bastar",                   // District name
      "problem_id": 123,                      // Problem ID (optional)
      "source": "cultural_stories"            // Data source
    },
    ...
  ],
  "total_results": 5
}
```

#### Example

**cURL:**
```bash
curl -X POST http://localhost:8000/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "राशन कार्ड नहीं बना रहा",
    "top_k": 3,
    "similarity_threshold": 0.5
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/knowledge/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "राशन कार्ड नहीं बना रहा",
        "top_k": 3,
        "similarity_threshold": 0.5
    }
)

data = response.json()
print(f"Found {data['total_results']} similar cases")
```

**JavaScript/TypeScript:**
```typescript
const response = await fetch('http://localhost:8000/v1/knowledge/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: 'राशन कार्ड नहीं बना रहा',
    top_k: 3,
    similarity_threshold: 0.5
  })
});

const data = await response.json();
console.log(`Found ${data.total_results} similar cases`);
```

---

### 2. Auto-Tag Suggestion

Automatically suggest problem category based on semantic similarity.

```http
POST /v1/knowledge/auto-tag
```

#### Request

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>`

**Body:**
```json
{
  "description": "string"    // Required: Problem description (Hindi/English)
}
```

#### Response

**Status:** 200 OK

```json
{
  "suggested_tag": "WATER_PROBLEM",    // Suggested category (null if no match)
  "confidence": 0.89,                  // Confidence score (0-1)
  "similar_cases_count": 5             // Number of similar cases found
}
```

**Note:** Returns `suggested_tag: null` if confidence < 0.7

#### Example

**cURL:**
```bash
curl -X POST http://localhost:8000/v1/knowledge/auto-tag \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "description": "हमारे गाँव में हैंडपंप ख़राब हो गया है और पीने के लिए पानी नहीं है"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/knowledge/auto-tag",
    headers={"Authorization": f"Bearer {token}"},
    json={"description": "हमारे गाँव में हैंडपंप ख़राब हो गया है"}
)

data = response.json()
if data['suggested_tag']:
    print(f"Suggested tag: {data['suggested_tag']} (confidence: {data['confidence']:.2%})")
else:
    print("No confident tag suggestion")
```

---

### 3. Vector Database Statistics

Get vector database statistics and health metrics.

```http
GET /v1/knowledge/stats
```

#### Request

**Headers:**
- `Authorization: Bearer <token>`

#### Response

**Status:** 200 OK

```json
{
  "total_vectors": 77,
  "dimension": 768,
  "model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
  "index_exists": true,
  "metadata_count": 77
}
```

#### Example

**cURL:**
```bash
curl http://localhost:8000/v1/knowledge/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/v1/knowledge/stats",
    headers={"Authorization": f"Bearer {token}"}
)

stats = response.json()
print(f"Total vectors: {stats['total_vectors']}")
print(f"Model: {stats['model']}")
```

---

### 4. Health Check

Check if the knowledge base service is operational.

```http
GET /v1/knowledge/health
```

#### Request

**Headers:**
- `Authorization: Bearer <token>`

#### Response

**Status:** 200 OK

```json
{
  "status": "healthy",                          // "healthy", "degraded", or "unhealthy"
  "vector_count": 77,
  "message": "Knowledge base is operational"
}
```

**Status Values:**
- `healthy`: Index loaded and contains vectors
- `degraded`: Index exists but empty
- `unhealthy`: Error loading index

#### Example

**cURL:**
```bash
curl http://localhost:8000/v1/knowledge/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/v1/knowledge/health",
    headers={"Authorization": f"Bearer {token}"}
)

health = response.json()
print(f"Status: {health['status']}")
```

---

## Error Responses

### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized

Missing or invalid authentication token.

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

User doesn't have permission to access resource.

```json
{
  "detail": "Not authorized"
}
```

### 500 Internal Server Error

Server error during processing.

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Limit**: 100 requests per minute per user
- **Header**: `X-RateLimit-Remaining` shows remaining requests
- **Exceeded**: Returns HTTP 429 Too Many Requests

---

## Data Models

### SearchRequest
```typescript
interface SearchRequest {
  query: string;                // Search query (Hindi/English)
  top_k?: number;              // Number of results (1-20), default: 5
  similarity_threshold?: number; // Min similarity (0.0-1.0), default: 0.0
}
```

### SearchResult
```typescript
interface SearchResult {
  similarity_score: number;     // Similarity score (0-1)
  description: string;          // Problem description
  tag: string | null;          // Problem category
  district: string | null;     // District name
  problem_id: number | null;   // Problem ID
  source: string;              // Data source
}
```

### SearchResponse
```typescript
interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}
```

### AutoTagRequest
```typescript
interface AutoTagRequest {
  description: string;          // Problem description
}
```

### AutoTagResponse
```typescript
interface AutoTagResponse {
  suggested_tag: string | null; // Suggested category
  confidence: number;           // Confidence score (0-1)
  similar_cases_count: number;  // Number of similar cases
}
```

### VectorDBStats
```typescript
interface VectorDBStats {
  total_vectors: number;
  dimension: number;
  model: string;
  index_exists: boolean;
  metadata_count: number;
}
```

---

## Best Practices

### 1. Similarity Threshold

- **Low threshold (0.0-0.4)**: Broad matching, may include unrelated cases
- **Medium threshold (0.5-0.7)**: Balanced matching (recommended)
- **High threshold (0.8-1.0)**: Strict matching, only very similar cases

### 2. Top-K Selection

- **top_k=1-3**: Quick similarity check, duplicate detection
- **top_k=3-5**: Standard RAG context (recommended)
- **top_k=10-20**: Comprehensive analysis, pattern detection

### 3. Query Optimization

- **Use full sentences**: "गाँव में पानी की समस्या है" (better) vs "पानी" (worse)
- **Include context**: "हैंडपंप ख़राब है" (better) vs "ख़राब" (worse)
- **Natural language**: Write as you would speak

### 4. Error Handling

```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    results = response.json()
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
except ValueError as e:
    print(f"JSON decode error: {e}")
```

---

## Interactive Documentation

Visit `http://localhost:8000/docs` for:
- Interactive Swagger UI
- Try API endpoints directly in browser
- View request/response schemas
- Test authentication

---

## Support

- **GitHub Issues**: [Report Bugs](https://github.com/your-org/boloo-app/issues)
- **Documentation**: [RAG README](README.md)
- **Email**: support@boloo.com

---

**Version**: 1.0.0
**Last Updated**: November 14, 2025
