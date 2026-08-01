# SmartLearn Agent — Product Design

## User Stories

| # | As a… | I want to… | So that… |
|---|-------|------------|----------|
| 1 | student | upload a lecture PDF and ask questions about concepts I don't understand | I can get instant, personalized explanations without waiting for office hours |
| 2 | student | generate a concise study guide from my course materials before an exam | I can review key points efficiently instead of re-reading hundreds of slides |
| 3 | teacher | see which topics students ask about most frequently | I can identify pain points in my lectures and improve them for next semester |

---

## Feature List

### P0 — Must Have (Day 2)
| # | Feature | Description |
|---|---------|-------------|
| F1 | PDF Upload & Text Extraction | Upload a PDF, extract all readable text, and store it for analysis |
| F2 | Q&A with Citations | Ask a question and get an answer with [Page X] citations pointing to the source |
| F3 | Summary Generation | Generate an overview, key points, and limitations from a PDF |

### P1 — Should Have (Day 2–3)
| # | Feature | Description |
|---|---------|-------------|
| F4 | Multi-PDF Management | Upload and manage multiple PDFs; switch between them when asking questions |
| F5 | Chat History | Keep conversation history so follow-up questions have context |
| F6 | Web UI | Browser-based interface (React frontend + FastAPI backend) |

### P2 — Nice to Have (Day 3+)
| # | Feature | Description |
|---|---------|-------------|
| F7 | RAG with FAISS | Chunk text → embed → store in vector DB → retrieve relevant chunks for more accurate answers |
| F8 | Analytics Dashboard | Show teachers which topics get the most questions |
| F9 | Export Study Guides | Download summaries as PDF or Markdown |

### What We Will NOT Build
- Real-time collaborative editing
- Mobile app
- OCR for scanned/handwritten PDFs
- Support for non-PDF formats (video, audio)

---

## Data Flow Diagrams

### Day 2 — Simple Mode (Direct Injection)

```
PDF File
    |
    v
+-------------+
| Extract Text|  PyMuPDF reads all pages
|  (PyMuPDF)  |
+------+------+
       |  full text + page numbers
       v
+-------------+
|  Build      |  System prompt + numbered text + user question
|  Prompt     |
+------+------+
       |  messages array
       v
+-------------+
|  LLM Call   |  OpenRouter (google/gemma-4-26b-a4b-it:free)
| (OpenRouter)|
+------+------+
       |  response text
       v
+-------------+
|  Display    |  Answer with [Page X] citations
|  Answer     |
+------+------+
       |
       v
     User
```

### Day 3 — RAG Mode (Vector Search)

```
PDF File
    |
    v
+-------------+
|  Chunk Text |  Split into overlapping segments (~500 tokens each)
|  (Splitter) |
+------+------+
       |  chunks
       v
+-------------+
|  Embed      |  Convert each chunk to a vector (text-embedding-3-small)
|  (Embedder) |
+------+------+
       |  vectors
       v
+-------------+
|  Store      |  Store vectors in FAISS index with chunk metadata
|  (FAISS)    |
+------+------+
       |
       |  +----------+
       |  |  Query   |  User asks a question
       |  +----+-----+
       |       |  question text
       |       v
       |  +----------+
       |  |  Embed   |  Convert question to vector
       |  |  Query   |
       |  +----+-----+
       |       |  query vector
       |       v
       |  +----------+
       |  | Retrieve |  Find top-K most similar chunks
       |  | (FAISS)  |
       |  +----+-----+
       |       |  relevant chunks
       |       v
       |  +----------+
       |  |  Build   |  System prompt + retrieved chunks + citations + question
       |  |  Prompt  |
       |  +----+-----+
       |       |  messages array
       |       v
       |  +----------+
       |  |  LLM     |  OpenRouter generates answer from retrieved context
       |  |  Call    |
       |  +----+-----+
       |       |  response text
       |       v
       |  +----------+
       |  |  Display |  Answer with [Page X] citations
       |  |  Answer  |
       |  +----+-----+
       |       |
       |       v
       |     User
```
