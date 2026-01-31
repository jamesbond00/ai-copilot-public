# Wiki Setup Guide for AI Copilot Project

This guide provides options for setting up a local wiki for your AI Copilot monitoring/logging system documentation.

## Option 1: Wiki.js (Recommended)

Wiki.js is modern, fast, and perfect for technical documentation.

### Quick Docker Setup

```bash
# Create wiki directory
mkdir -p /Users/alex/ai-copilot/wiki
cd /Users/alex/ai-copilot/wiki

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  wiki:
    image: requarks/wiki:2
    container_name: ai-copilot-wiki
    ports:
      - "3000:3000"
    environment:
      - DB_TYPE=postgres
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=wikijs
      - DB_PASS=wikijspassword
      - DB_NAME=wiki
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: ai-copilot-wiki-db
    environment:
      - POSTGRES_DB=wiki
      - POSTGRES_USER=wikijs
      - POSTGRES_PASSWORD=wikijspassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Start the wiki
docker-compose up -d

# Access at http://localhost:3000
```

### Features Perfect for AI Copilot:
- Markdown support for code documentation
- Syntax highlighting for Python/JavaScript
- Search functionality
- User management
- API documentation templates

## Option 2: BookStack

Simple, clean interface with WYSIWYG editor.

### Docker Setup

```bash
# Create bookstack directory
mkdir -p /Users/alex/ai-copilot/bookstack
cd /Users/alex/ai-copilot/bookstack

cat > docker-compose.yml << EOF
version: '3.8'

services:
  bookstack:
    image: lscr.io/linuxserver/bookstack:latest
    container_name: ai-copilot-bookstack
    environment:
      - PUID=1000
      - PGID=1000
      - APP_URL=http://localhost:8080
      - DB_HOST=bookstack_db
      - DB_USER=bookstack
      - DB_PASS=bookstackpassword
      - DB_DATABASE=bookstack
    volumes:
      - bookstack_data:/config
    ports:
      - "8080:80"
    depends_on:
      - bookstack_db
    restart: unless-stopped

  bookstack_db:
    image: lscr.io/linuxserver/mariadb:latest
    container_name: ai-copilot-bookstack-db
    environment:
      - PUID=1000
      - PGID=1000
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=bookstack
      - MYSQL_USER=bookstack
      - MYSQL_PASSWORD=bookstackpassword
    volumes:
      - bookstack_db_data:/config
    restart: unless-stopped

volumes:
  bookstack_data:
  bookstack_db_data:
EOF

docker-compose up -d
# Access at http://localhost:8080
```

## Option 3: Outline (Modern, Notion-like)

```bash
# Create outline directory
mkdir -p /Users/alex/ai-copilot/outline
cd /Users/alex/ai-copilot/outline

cat > docker-compose.yml << EOF
version: '3.8'

services:
  outline:
    image: outlinewiki/outline:latest
    container_name: ai-copilot-outline
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://outline:outlinepassword@postgres:5432/outline
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key-here
      - UTILS_SECRET=your-utils-secret-here
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:13-alpine
    container_name: ai-copilot-outline-db
    environment:
      - POSTGRES_USER=outline
      - POSTGRES_PASSWORD=outlinepassword
      - POSTGRES_DB=outline
    volumes:
      - outline_db_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    container_name: ai-copilot-outline-redis
    volumes:
      - outline_redis_data:/data
    restart: unless-stopped

volumes:
  outline_db_data:
  outline_redis_data:
EOF

docker-compose up -d
```

## Integration with Your AI Copilot Project

### Suggested Wiki Structure

```
AI Copilot Documentation/
├── Getting Started/
│   ├── Installation Guide
│   ├── Configuration
│   └── Quick Start
├── Architecture/
│   ├── System Overview
│   ├── Data Flow
│   └── Component Details
├── API Documentation/
│   ├── FastAPI Endpoints
│   ├── Data Schemas
│   └── Authentication
├── Monitoring & Logging/
│   ├── ELK Stack Integration
│   ├── Prometheus Metrics
│   └── Alert Configuration
├── LLM Integration/
│   ├── Model Configuration
│   ├── Prompt Engineering
│   └── Response Formatting
└── Development/
    ├── Testing Guide
    ├── Contributing
    └── Troubleshooting
```

### Auto-Generated Documentation

You can integrate your wiki with your existing FastAPI application:

```python
# Add to src/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="AI Copilot API",
    description="Intelligent monitoring and logging assistant",
    version="0.1.0"
)

# Mount wiki if using static files
# app.mount("/docs", StaticFiles(directory="wiki/docs"), name="docs")
```

## Recommendations for Your Project

**For AI Copilot, I recommend Wiki.js because:**

1. **Technical Documentation**: Excellent Markdown support for API docs
2. **Code Integration**: Syntax highlighting for Python/JavaScript
3. **Search**: Built-in search for finding monitoring queries and configurations
4. **Version Control**: Git integration for documentation versioning
5. **API Access**: REST API for programmatic content updates
6. **Docker Ready**: Easy deployment alongside your existing services

## Next Steps

1. Choose your preferred wiki solution
2. Run the Docker setup
3. Create initial documentation structure
4. Integrate with your existing FastAPI application
5. Set up automated documentation generation

## Access URLs

- **Wiki.js**: http://localhost:3000
- **BookStack**: http://localhost:8080  
- **Outline**: http://localhost:3000

Choose the one that best fits your team's workflow and documentation needs!
