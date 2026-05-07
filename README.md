# Assignment 4 – NCU Regulation Assistant

## Overview

This project implements a lightweight Knowledge Graph (KG) based regulation assistant for NCU regulations using:

- SQLite for structured regulation storage
- Neo4j for graph representation
- HuggingFace local LLM (`Qwen2.5-3B-Instruct`)
- Python 3.11
- Docker (Neo4j)

The system parses PDF regulations, builds a knowledge graph, retrieves relevant regulation content, and generates grounded answers using a local language model.

---

# Project Structure

```text
Assignment-4-main/
│
├── source/                 # Raw regulation PDFs
├── setup_data.py           # PDF parsing + SQLite generation
├── build_kg.py             # Neo4j graph construction
├── query_system.py         # Interactive chatbot
├── auto_test.py            # Benchmark evaluation
├── llm_loader.py           # Local HuggingFace model loader
├── requirements.txt
├── ncu_regulations.db
└── hf_model_cache/
```

---

# Environment Setup

## Requirements

- Python 3.11
- Docker Desktop
- Internet connection (first HuggingFace download only)

---

# 1. Start Neo4j with Docker

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

Neo4j Browser:

```text
http://localhost:7474
```

Credentials:

```text
Username: neo4j
Password: password
```

---

# 2. Create Virtual Environment

## Windows

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

---

# 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Execution Order

## Step 1 — Parse Regulations

```bash
python setup_data.py
```

This step:
- parses PDFs using `pdfplumber`
- extracts regulation articles
- stores structured data into SQLite

---

## Step 2 — Build Knowledge Graph

```bash
python build_kg.py
```

This step:
- creates `Regulation`, `Article`, and `Rule` nodes
- creates relationships:

```text
(Regulation)-[:HAS_ARTICLE]->(Article)-[:CONTAINS_RULE]->(Rule)
```

- creates Neo4j full-text indexes

---

## Step 3 — Run Interactive Assistant

```bash
python query_system.py
```

Example questions:

```text
What happens if a student forgets their ID card?
What are the examination rules?
student ID
```

---

## Step 4 — Run Benchmark Evaluation

```bash
python auto_test.py
```

This script automatically evaluates:
- Neo4j graph integrity
- Rule coverage
- QA pipeline performance

---

# Knowledge Graph Schema

## Regulation Node

```text
Regulation {
    id,
    name,
    category
}
```

## Article Node

```text
Article {
    number,
    content,
    reg_name,
    category
}
```

## Rule Node

```text
Rule {
    rule_id,
    type,
    action,
    result,
    art_ref,
    reg_name
}
```

---

# Retrieval Pipeline

The chatbot pipeline follows:

```text
User Question
    ↓
Keyword Extraction
    ↓
Neo4j Retrieval
    ↓
Top-K Relevant Articles
    ↓
Prompt Construction
    ↓
Local LLM Generation
```

---

# Model

Local HuggingFace model used:

```text
Qwen/Qwen2.5-3B-Instruct
```

The model is automatically downloaded during the first execution and cached locally.

---

# Notes

- First model download may take several minutes (~6GB).
- The model runs locally on CPU.
- Neo4j must be running before executing the scripts.
- The system uses grounded generation based only on retrieved regulation content.

---

# Authors

NCU Assignment 4 – Knowledge Graph Regulation Assistant
