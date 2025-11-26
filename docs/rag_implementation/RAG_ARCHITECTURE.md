# RAG (Retrieval Augmented Generation) Architecture for Boloo App

## Executive Summary

**What**: Convert 78 historical Bastar problems/stories from Excel to vector database and implement RAG for enhanced AI responses

**Why**: Provide context-aware, culturally-relevant responses based on historical problem resolutions

**How**: FAISS vector DB + sentence-transformers + Azure OpenAI integration

---

## 📊 Data Analysis

### File 1: `bastar problems (1).xlsx`
- **Records**: 29 CGNet problems from Bastar district
- **Language**: Hindi (primary)
- **Content**: Real grievances (toilet, pension, ration card, water supply)
- **Status**: 28 "Not Assigned", 1 other
- **Metadata**: District, State, Location, Contact numbers, Resolution dates

### File 2: `bastar problems latest_rag.xlsx`
- **Records**: 49 tagged problems prepared for RAG
- **Language**: Hindi
- **Tagged Categories**:
  - WATER_PROBLEM (27 cases - 55%)
  - ROAD_PROBLEM (10 cases - 20%)
  - RATION_CARD_PROBLEM (8 cases - 16%)
  - ANGANWADI_PROBLEM (2 cases)
  - GAS_PROBLEM_BASTAR (1 case)
  - ELECTRICITY_PROBLEM (1 case)

**Total Knowledge Base**: 78 historical problems/resolutions

---

## 🏗️ Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Conversation Flow                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               1. Extract Problem Description                     │
│                  (from conversation turns)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               2. Generate Embedding (768-dim)                    │
│              sentence-transformers/paraphrase-multilingual       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            3. Semantic Search in Vector DB (FAISS)               │
│                  Find top-k similar cases (k=3-5)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              4. Construct RAG Context for GPT-4o                 │
│    "Similar problems resolved before: [case1, case2, case3]"     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│         5. Azure OpenAI GPT-4o Enhanced Response                 │
│   Context-aware answer based on historical resolutions           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Components

### 1. Vector Database: FAISS
**Why FAISS?**
- ✅ Local deployment (no external API costs)
- ✅ Fast similarity search (< 10ms for 78 vectors)
- ✅ Low memory footprint (~1MB for 78 vectors)
- ✅ No internet dependency
- ✅ Open source (Facebook Research)

**Alternative**: PostgreSQL with pgvector (already have Postgres running)

### 2. Embedding Model: sentence-transformers
**Model**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- ✅ **Multilingual support** (Hindi + English)
- ✅ 768-dimensional embeddings
- ✅ Semantic understanding
- ✅ Already installed (v2.2.2)
- ✅ 420M parameters (runs on CPU)

### 3. Storage Schema

**Vector Store**:
```python
{
  "id": "problem_001",
  "embedding": [0.234, -0.567, ...],  # 768-dim vector
  "metadata": {
    "description": "पालानार, डोंगरी पारा से राशन कार्ड नहीं बना...",
    "district": "Bastar",
    "tag": "RATION_CARD_PROBLEM",
    "date": "2020-09-21",
    "problem_id": 123,
    "source": "cgnet_problems"
  }
}
```

**PostgreSQL Extension** (optional backup):
```sql
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    problem_id INTEGER UNIQUE,
    description TEXT NOT NULL,
    embedding VECTOR(768),  -- pgvector extension
    district VARCHAR(100),
    tag VARCHAR(50),
    date DATE,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

---

## 🎯 Implementation Plan

### Phase 1: Data Ingestion (scripts/data_ingestion/)
1. **Excel to JSON converter** (`ingest_excel_to_json.py`)
2. **Embedding generator** (`generate_embeddings.py`)
3. **FAISS index builder** (`build_faiss_index.py`)
4. **PostgreSQL backup** (`sync_to_postgres.py`)

### Phase 2: RAG Service (backend/app/services/rag/)
1. **Vector search service** (`vector_search.py`)
2. **Context builder** (`context_builder.py`)
3. **RAG orchestrator** (`rag_service.py`)

### Phase 3: Integration (backend/app/routers/)
1. **Chat router integration** - Add RAG context to prompts
2. **Semantic search endpoint** - `/v1/knowledge/search`
3. **Admin ingestion endpoint** - `/v1/admin/knowledge/ingest`

### Phase 4: Testing & Optimization
1. **Relevance testing** - Measure retrieval accuracy
2. **Performance testing** - Latency benchmarks
3. **A/B testing** - With/without RAG comparison

---

## 📈 Expected Benefits

### 1. Context-Aware Responses ⭐⭐⭐⭐⭐
**Before RAG**:
```
User: "मेरे गाँव में पानी की समस्या है"
AI: "कृपया अपनी समस्या का विवरण दें। पानी की समस्या किस प्रकार की है?"
```

**After RAG**:
```
User: "मेरे गाँव में पानी की समस्या है"
AI (with context from 27 similar water problems):
"मैं समझता हूं। बस्तर में इससे पहले 27 समान पानी की समस्याएं दर्ज की गई हैं।
अक्सर यह समस्या:
- हैंडपंप खराब होने से
- सोलर पंप की समस्या
- नाले के पानी पर निर्भरता

क्या आपकी समस्या इनमें से किसी से मेल खाती है? कृपया विवरण दें।"
```

### 2. Intelligent Question Suggestions ⭐⭐⭐⭐
- Suggest relevant follow-up questions based on similar cases
- Ask about common resolution factors (e.g., "क्या सरपंच से संपर्क किया?")

### 3. Faster Problem Classification ⭐⭐⭐⭐⭐
- Auto-tag problems based on semantic similarity
- Reduce manual classification effort

### 4. Better Completeness Detection ⭐⭐⭐⭐
- Compare current case against historical complete cases
- Identify missing critical fields

### 5. Resolution Pattern Learning ⭐⭐⭐⭐
- Show successful resolution examples
- Guide users through proven resolution paths

---

## 🚀 Additional Use Cases

### 1. Similar Case Finder (Moderator Tool)
**Endpoint**: `GET /v1/knowledge/similar?description=...`
```json
{
  "query": "पानी की समस्या है गाँव में",
  "similar_cases": [
    {
      "similarity_score": 0.92,
      "description": "ग्राम-पटेलपारा में पानी की समस्या...",
      "tag": "WATER_PROBLEM",
      "resolution_time_days": 15
    }
  ]
}
```

### 2. Auto-Tagging Service
```python
def auto_tag_case(description: str) -> str:
    """Tag case based on most similar historical case"""
    similar = vector_search(description, top_k=1)
    return similar[0]['metadata']['tag']
```

### 3. Duplicate Detection
- Prevent duplicate case creation
- Merge similar ongoing cases
- Alert user: "आपकी समस्या से मिलती-जुलती 3 शिकायतें पहले से दर्ज हैं"

### 4. Trend Analysis Dashboard
```python
# Analyze problem clusters by district
problems_by_district = analyze_embeddings_clustering()
# Output: "Bastar में 55% पानी की समस्याएं हैं"
```

### 5. Chatbot Training Data
- Use historical conversations for fine-tuning
- Improve response quality over time
- Learn Bastar-specific vocabulary

### 6. Expected Resolution Time Prediction
```python
def predict_resolution_time(description: str) -> int:
    """Predict days to resolution based on similar cases"""
    similar_cases = vector_search(description, top_k=10)
    avg_days = mean([c['resolution_time'] for c in similar_cases])
    return avg_days
```

### 7. Multi-Language Support
- Embed English translations alongside Hindi
- Support cross-language similarity search
- Help English-speaking moderators understand Hindi cases

---

## 🔬 Technical Specifications

### Embedding Generation
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

# Generate embedding
text = "पानी की समस्या है गाँव में"
embedding = model.encode(text)  # Shape: (768,)
```

### FAISS Index Creation
```python
import faiss
import numpy as np

# Create FAISS index (Flat L2 for small dataset)
dimension = 768
index = faiss.IndexFlatL2(dimension)  # Or IndexFlatIP for cosine

# Add vectors
embeddings_matrix = np.array([emb1, emb2, ...])  # Shape: (78, 768)
index.add(embeddings_matrix)

# Save index
faiss.write_index(index, "knowledge_base.index")
```

### Semantic Search
```python
# Search for top-k similar vectors
query_embedding = model.encode("नया पानी की समस्या")
k = 3
distances, indices = index.search(query_embedding.reshape(1, -1), k)

# distances: cosine similarity scores
# indices: indices of similar vectors
```

---

## 📊 Performance Metrics

### Expected Performance:
- **Embedding generation**: ~50ms per problem (CPU)
- **Vector search**: < 10ms for 78 vectors
- **Total RAG latency**: < 100ms (negligible impact on API)
- **Storage**:
  - FAISS index: ~1MB (78 vectors × 768 dim × 4 bytes)
  - PostgreSQL: ~500KB metadata

### Scalability:
- **Current**: 78 problems (baseline)
- **1 year**: ~5,000 problems (< 100ms search)
- **5 years**: ~25,000 problems (< 200ms search)
- **FAISS IVF** (when > 10K): Sub-100ms with IVF clustering

---

## 🛠️ Development Phases

### Week 1: Foundation
- ✅ Install FAISS (`pip install faiss-cpu`)
- ✅ Data ingestion scripts
- ✅ Embedding generation pipeline
- ✅ FAISS index creation

### Week 2: Integration
- ✅ RAG service implementation
- ✅ Chat router integration
- ✅ Semantic search endpoint

### Week 3: Testing & Refinement
- ✅ Relevance testing
- ✅ Performance benchmarks
- ✅ User acceptance testing

### Week 4: Production Deployment
- ✅ Index versioning system
- ✅ Auto-reindex pipeline
- ✅ Monitoring & logging

---

## 🎓 Fine-Tuning Considerations

**Current Approach**: RAG (retrieval only)
**Future Enhancement**: Fine-tuning GPT-4o-mini

### Fine-Tuning Dataset Requirements:
1. **Conversation pairs**: (User message → AI response)
2. **Minimum**: 50-100 quality examples
3. **Format**: JSONL with system/user/assistant roles

### When to Fine-Tune:
- **After 6 months** of RAG usage
- When we have **500+ high-quality conversations**
- To learn **Bastar-specific language patterns**
- To improve **response consistency**

**Cost**: ~$0.80 per 1K training tokens (Azure OpenAI)

---

## 🔐 Security & Privacy

1. **Data Anonymization**: Remove contact numbers before embedding
2. **Access Control**: Only authenticated users can query knowledge base
3. **Audit Logging**: Track all RAG retrievals
4. **No PII in Embeddings**: Strip personal identifiable information

---

## 📚 Dependencies

```txt
# Already installed:
openai==1.10.0
sentence-transformers==2.2.2

# New dependencies:
faiss-cpu==1.7.4  # Vector search
numpy==1.24.3  # Array operations
pandas==2.0.3  # Data processing
```

---

## 🎯 Success Metrics

1. **Retrieval Accuracy**: > 80% relevant results in top-3
2. **User Satisfaction**: +20% improvement in response quality ratings
3. **Completeness Score**: +15% average (better questions → more info)
4. **Response Latency**: < 100ms RAG overhead
5. **Duplicate Reduction**: -30% duplicate case creation

---

## 🔄 Continuous Improvement

### Auto-Learning Pipeline:
1. **Weekly**: Ingest new resolved cases into vector DB
2. **Monthly**: Retrain embeddings with updated model
3. **Quarterly**: A/B test RAG parameters (top_k, similarity threshold)

### Feedback Loop:
```
User Conversation → Case Created → Resolved
                         ↓
                   Add to Vector DB
                         ↓
              Improve Future Responses
```

---

**Status**: Architecture Designed ✅
**Next Step**: Implementation (Phase 1 - Data Ingestion)
