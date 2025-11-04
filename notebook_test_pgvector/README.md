# pgvector RAG Test Notebook

This directory contains everything needed to test pgvector-based RAG implementation before migrating from ChromaDB.

## 📁 Files

- **`rag_pgvector.ipynb`** - Main Jupyter notebook for testing pgvector RAG
- **`eTMS USER GUIDE DOCUMENT.pdf`** - Test PDF document (54MB)
- **`PGVECTOR_SETUP_GUIDE.md`** - Comprehensive installation guide
- **`install_pgvector_windows.ps1`** - Automated Windows installation script
- **`docker-compose-pgvector.yml`** - Docker setup (easiest option)
- **`init.sql`** - Database initialization script

## 🚀 Quick Start

### Option 1: Docker (Recommended - Easiest)

**Prerequisites**: Docker Desktop installed

```bash
# Start PostgreSQL with pgvector
docker-compose -f docker-compose-pgvector.yml up -d

# Verify it's running
docker-compose -f docker-compose-pgvector.yml ps

# View logs
docker-compose -f docker-compose-pgvector.yml logs -f
```

Then update the notebook's `DB_CONFIG` to use port `5433`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # Docker container port
    'database': 'agenthub_chatbot_test',
    'user': 'postgres',
    'password': 'postgres'
}
```

### Option 2: Install pgvector on Existing PostgreSQL

**Method A: Automated (Windows)**

Run PowerShell as Administrator:

```powershell
cd notebook_test_pgvector
.\install_pgvector_windows.ps1
```

**Method B: Manual Installation**

See detailed instructions in [`PGVECTOR_SETUP_GUIDE.md`](PGVECTOR_SETUP_GUIDE.md)

## 📓 Running the Notebook

### 1. Install Python Dependencies

```bash
pip install psycopg2-binary sentence-transformers pypdf2 numpy pandas tqdm langchain-community jupyter
```

### 2. Set Database Password (Optional)

```bash
# Windows
set DB_PASSWORD=your_password

# Linux/Mac
export DB_PASSWORD=your_password
```

### 3. Start Jupyter

```bash
cd notebook_test_pgvector
jupyter notebook rag_pgvector.ipynb
```

### 4. Run All Cells

Execute cells sequentially to:
1. Install dependencies
2. Connect to PostgreSQL
3. Enable pgvector extension
4. Create document table with vector column
5. Extract text from PDF (eTMS USER GUIDE)
6. Chunk documents (500 chars with 50 char overlap)
7. Generate embeddings (all-MiniLM-L6-v2, 384 dimensions)
8. Store vectors in PostgreSQL
9. Create HNSW index for fast similarity search
10. Test search with sample queries
11. View performance statistics

## 📊 Expected Results

After running all cells, you should see:

- **Document Statistics**: Total pages, chunks, avg chunks per page
- **Embedding Shape**: (N, 384) where N = number of chunks
- **Search Performance**: ~10-50ms per query (depending on hardware)
- **Similarity Scores**: 0.0 to 1.0 (higher = more similar)

Example output:

```
📄 Document Statistics:
  - Total Pages: 150
  - Total Chunks: 450
  - Avg Chunks/Page: 3.0

🔨 HNSW index created in 2.34 seconds

🔍 Testing similarity search...
Query: 'How do I track shipments?'
⏱️ Search time: 23.45ms

Result 1 (Score: 0.8234)
Page 42, Chunk 0
Text: To track shipments in eTMS, navigate to the Shipment Tracking module...
```

## 🐛 Troubleshooting

### Error: "extension 'vector' is not available"

**Solution**: pgvector is not installed. Follow [`PGVECTOR_SETUP_GUIDE.md`](PGVECTOR_SETUP_GUIDE.md)

### Error: "PDF not found"

**Cause**: Notebook can't find `eTMS USER GUIDE DOCUMENT.pdf`

**Solution**:
- Ensure PDF is in the same directory as notebook
- Or update `PDF_PATH` variable in Cell 5

### Error: "Connection failed"

**Cause**: Wrong database credentials or PostgreSQL not running

**Solution**:
- Verify PostgreSQL is running: `Get-Service *postgres*` (Windows)
- Check connection parameters in `DB_CONFIG`
- Ensure database exists: `psql -U postgres -l`

### Error: "Out of memory" during embedding generation

**Cause**: Too many chunks or limited RAM

**Solution**: Process in smaller batches:

```python
# In Cell 6, modify:
batch_size = 16  # Reduce from 32
embeddings = embedding_model.encode(chunk_texts, batch_size=batch_size, ...)
```

## 📋 Next Steps After Testing

1. **Review Results**: Evaluate search quality and performance
2. **Compare with ChromaDB**: Test same queries on current system
3. **Proceed with Migration**: Follow [`Documentation/PGVECTOR_MIGRATION_PLAN.md`](../Documentation/PGVECTOR_MIGRATION_PLAN.md)
4. **Update Backend Agents**: Integrate pgvector into production chatbot

## 🔗 Additional Resources

- **pgvector GitHub**: https://github.com/pgvector/pgvector
- **sentence-transformers**: https://www.sbert.net/
- **HNSW Algorithm**: https://arxiv.org/abs/1603.09320
- **Migration Plan**: [`../Documentation/PGVECTOR_MIGRATION_PLAN.md`](../Documentation/PGVECTOR_MIGRATION_PLAN.md)

## 💡 Tips

### Optimizing Search Performance

- **Index Parameters**: Adjust `m` and `ef_construction` in HNSW index
  - Higher `m` = better recall, slower build
  - Higher `ef_construction` = better quality, slower build

- **Chunk Size**: Experiment with different sizes (300-1000 chars)
  - Smaller chunks = more precise, more storage
  - Larger chunks = more context, fewer chunks

- **Embedding Model**: Try different models:
  - `all-MiniLM-L6-v2` (384d) - Fast, good quality
  - `all-mpnet-base-v2` (768d) - Better quality, slower
  - `multilingual-e5-base` (768d) - Multilingual support

### Database Optimization

```sql
-- Analyze table statistics
ANALYZE document_chunks;

-- Check index usage
SELECT * FROM pg_stat_user_indexes WHERE relname = 'document_chunks';

-- View table size
SELECT pg_size_pretty(pg_total_relation_size('document_chunks'));
```

## 📝 Notes

- **Test Environment**: This notebook uses a separate test database to avoid affecting production
- **PDF Size**: The eTMS USER GUIDE is 54MB - processing may take 1-2 minutes
- **Docker Port**: Uses port `5433` to avoid conflicts with existing PostgreSQL on `5432`
- **Cleanup**: Run the optional cleanup cell at the end to drop test table

---

**Status**: Ready for Testing
**Created**: 2025-11-03
**Purpose**: Test pgvector RAG before full ChromaDB migration
