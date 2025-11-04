# pgvector Installation Guide for Windows

**Issue**: `extension "vector" is not available`

**Solution**: Install pgvector extension for PostgreSQL

---

## Method 1: Using Pre-built Windows Binaries (Recommended - Easiest)

### Step 1: Download pgvector Binary

1. Visit: https://github.com/pgvector/pgvector/releases
2. Download the Windows binary for your PostgreSQL version (e.g., `pgvector-0.7.0-pg16-windows-x64.zip`)
3. Extract the ZIP file

### Step 2: Install the Extension

Copy the extracted files to your PostgreSQL installation directory:

```bash
# Find your PostgreSQL installation directory first
# Common locations:
# C:\Program Files\PostgreSQL\16\
# C:\PostgreSQL\16\
# C:\xampp\postgresql\

# Copy files:
# vector.dll -> C:\Program Files\PostgreSQL\16\lib\
# vector.control and vector--*.sql -> C:\Program Files\PostgreSQL\16\share\extension\
```

**PowerShell commands** (run as Administrator):

```powershell
# Example for PostgreSQL 16
$PG_HOME = "C:\Program Files\PostgreSQL\16"

# Copy DLL
Copy-Item "path\to\extracted\vector.dll" "$PG_HOME\lib\"

# Copy control and SQL files
Copy-Item "path\to\extracted\vector.control" "$PG_HOME\share\extension\"
Copy-Item "path\to\extracted\vector--*.sql" "$PG_HOME\share\extension\"
```

### Step 3: Enable Extension

Connect to your database and run:

```sql
CREATE EXTENSION vector;
```

---

## Method 2: Using Docker (Alternative - Clean Setup)

If you have Docker installed, you can use the official pgvector image:

### Step 1: Create Docker Compose File

Create `docker-compose.yml` in your project root:

```yaml
version: '3.8'

services:
  postgres-pgvector:
    image: pgvector/pgvector:pg16
    container_name: agenthub_postgres_pgvector
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: agenthub_chatbot
    ports:
      - "5432:5432"
    volumes:
      - pgvector_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgvector_data:
```

### Step 2: Start PostgreSQL with pgvector

```bash
docker-compose up -d
```

### Step 3: Verify Installation

```bash
docker exec -it agenthub_postgres_pgvector psql -U postgres -d agenthub_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

---

## Method 3: Build from Source (Advanced)

### Prerequisites

Install build tools on Windows:

1. **Visual Studio 2022** with C++ development tools
2. **PostgreSQL** with development headers

### Build Steps

```bash
# Clone repository
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Set PostgreSQL path
set "PGROOT=C:\Program Files\PostgreSQL\16"

# Build
nmake /F Makefile.win

# Install
nmake /F Makefile.win install
```

---

## Verification

After installation, verify pgvector is working:

### SQL Test

```sql
-- Connect to your database
psql -U postgres -d agenthub_chatbot

-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Test vector operations
CREATE TABLE test_vectors (id SERIAL PRIMARY KEY, embedding vector(3));
INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
SELECT * FROM test_vectors ORDER BY embedding <-> '[3,3,3]' LIMIT 1;

-- Cleanup
DROP TABLE test_vectors;
```

### Python Test

Run this in your notebook first cell:

```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='agenthub_chatbot',
    user='postgres',
    password='your_password'
)

with conn.cursor() as cur:
    # Try to create extension
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension enabled")

        # Check version
        cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        result = cur.fetchone()
        if result:
            print(f"✅ pgvector version: {result[1]}")
        else:
            print("❌ pgvector not found")
    except Exception as e:
        print(f"❌ Error: {e}")

conn.close()
```

---

## Troubleshooting

### Error: "extension "vector" is not available"

**Cause**: pgvector files not in PostgreSQL directories

**Solutions**:

1. **Check PostgreSQL version compatibility**:
   ```sql
   SELECT version();
   ```
   Download matching pgvector version

2. **Verify file locations**:
   ```bash
   # Check if files exist
   dir "C:\Program Files\PostgreSQL\16\lib\vector.dll"
   dir "C:\Program Files\PostgreSQL\16\share\extension\vector.control"
   ```

3. **Check PostgreSQL service**:
   - Restart PostgreSQL service after copying files
   - Services → PostgreSQL → Restart

4. **Permissions**:
   - Ensure files have correct permissions
   - Run installation commands as Administrator

### Error: "could not load library"

**Cause**: Missing dependencies or wrong architecture (32-bit vs 64-bit)

**Solution**:
- Ensure PostgreSQL and pgvector match (both 64-bit or both 32-bit)
- Install Visual C++ Redistributable 2015-2022

### Error: "permission denied"

**Cause**: Insufficient database privileges

**Solution**:
```sql
-- Grant superuser or create extension privilege
ALTER USER postgres CREATEDB;
-- Or connect as postgres user
```

---

## Quick Start for Your Project

### Option A: Use Docker (Recommended for Testing)

```bash
# Stop existing PostgreSQL if running on port 5432
# Start pgvector-enabled PostgreSQL
docker run -d \
  --name agenthub_pgvector \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=agenthub_chatbot \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Migrate your existing data
pg_dump -h localhost -U postgres agenthub_chatbot > backup.sql
psql -h localhost -U postgres -d agenthub_chatbot < backup.sql
```

### Option B: Install on Existing PostgreSQL

1. Download binary from: https://github.com/pgvector/pgvector/releases
2. Extract and copy files to PostgreSQL directories
3. Restart PostgreSQL service
4. Run `CREATE EXTENSION vector;` in your database

---

## Recommended Approach for Your Setup

Based on your Windows environment, I recommend:

1. **Download pre-built binary** from GitHub releases
2. **Find PostgreSQL installation**:
   ```powershell
   Get-Service *postgres* | Select-Object Name, DisplayName, Status
   ```
3. **Copy files** to PostgreSQL directories (as Administrator)
4. **Restart PostgreSQL service**
5. **Run CREATE EXTENSION** in your database

---

## After Installation

Once pgvector is installed, run your Jupyter notebook:

```bash
cd notebook_test_pgvector
jupyter notebook rag_pgvector.ipynb
```

The notebook will automatically verify pgvector is working in **Section 3**.

---

## Additional Resources

- **Official Documentation**: https://github.com/pgvector/pgvector
- **Windows Installation**: https://github.com/pgvector/pgvector#windows
- **Docker Image**: https://hub.docker.com/r/pgvector/pgvector
- **Troubleshooting**: https://github.com/pgvector/pgvector/issues

---

**Note**: If you encounter issues, please share:
1. PostgreSQL version: `SELECT version();`
2. Operating system: `ver` (Windows)
3. Installation method attempted
4. Exact error message

I can provide more specific guidance based on your setup.
