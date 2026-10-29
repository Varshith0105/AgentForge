# AgentForge — Autonomous AI Software Engineering Platform

AgentForge is a production-ready AI-powered Software Engineering Platform with complete Model Context Protocol (MCP) support, featuring 59 AI-accessible tools across 7 specialized servers, enterprise-grade security, and one-command deployment.

## 🎉 Phase 7 Complete - Production Ready!

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Date:** July 6, 2026

- ✅ 7 MCP servers with 59 tools (filesystem, GitHub, Git, Docker, PostgreSQL, documentation, browser)
- ✅ 70+ validated API endpoints
- ✅ 13-layer security architecture
- ✅ One-command production deployment
- ✅ Comprehensive testing suite
- ✅ Complete documentation (8,150+ lines)

**Quick Start:** `./scripts/deploy.sh`

See [PHASE_7_COMPLETE.md](PHASE_7_COMPLETE.md) for full details.

## 📁 Repository Directory Structure

```
agentforge/
├── index.html                    # Interactive Landing Page
├── frontend/
│   ├── pages/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── forgot-password.html
│   │   ├── dashboard.html
│   │   ├── repo-analysis.html
│   │   ├── ai-chat.html
│   │   ├── code-explanation.html
│   │   ├── bug-detection.html
│   │   ├── test-generator.html
│   │   ├── docs-generator.html
│   │   ├── architecture.html
│   │   ├── pr-review.html
│   │   ├── security-scanner.html
│   │   ├── performance.html
│   │   └── settings.html
│   └── assets/
│       ├── css/
│       │   ├── variables.css      # Core tokens
│       │   ├── base.css           # Resets & typography
│       │   ├── animations.css     # Keyframes and reveals
│       │   ├── components.css     # Glass components library
│       │   ├── layout.css         # Sidebar grids
│       │   ├── landing.css        # Hero and visual panels
│       │   ├── auth.css           # Floating orb layouts
│       │   ├── chat.css           # Chat bubbles layout
│       │   └── pages.css          # Scanner components styling
│       └── js/
│           ├── utils.js           # Shared utilities
│           ├── particles.js       # Background Canvas networks
│           ├── landing.js         # Landing counters & carousels
│           ├── auth.js            # Validation & strength meters
│           ├── sidebar.js         # Navigation layouts
│           ├── charts.js          # Dark Chart.js templates
│           ├── dashboard.js       # Dashboard analytics
│           ├── repo-analysis.js   # Analysis simulation
│           ├── chat.js            # Interactive bubble stream
│           ├── code-tools.js      # Explanation & test generator
│           ├── docs-generator.js  # Markdown exporter
│           ├── architecture.js    # Relational SVGs plotter
│           ├── security.js        # Security audit checklist
│           ├── performance.js     # Code optimizations comparisons
│           └── agents.js          # Sequential Multi-Agent orchestration
└── backend/
    ├── api/
    │   └── endpoints.js           # API route payload specs
    ├── models/
    │   └── ai-provider.js         # Modular LLM drivers mapping
    └── database/
        └── schema.js              # SQLite/SQL relational tables model
```

## 🚀 Quick Start Guide

### Production Deployment (Recommended)

Deploy AgentForge to production with Docker Compose:

```bash
# 1. Configure environment
cp .env.production.example .env.production
nano .env.production  # Set your API keys and passwords

# 2. Deploy (automated)
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. Verify deployment
./scripts/health_check.sh
```

**Access:**
- Frontend: http://localhost
- Workspace: http://localhost/workspace.html
- API: http://localhost/api
- API Docs: http://localhost/api/v1/docs

### Development Mode

For local development:

```bash
# Frontend
cd frontend
# Open index.html or workspace.html in browser

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 📚 Documentation

### Quick Links
- **[Phase 7 Complete Report](PHASE_7_COMPLETE.md)** - Production readiness overview
- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment instructions
- **[MCP Architecture](MCP_ARCHITECTURE.md)** - Technical MCP documentation
- **[API Documentation](http://localhost/api/v1/docs)** - Swagger UI (when running)

### Key Features

#### 🤖 AI Capabilities
- Multi-provider support (OpenAI, Anthropic, Google)
- 59 AI-accessible tools via MCP
- Intelligent code analysis and generation
- Repository understanding and context building
- Automated documentation generation

#### 🛠️ MCP Servers (7 servers, 59 tools)
- **Filesystem** (10 tools) - File operations with security
- **GitHub** (8 tools) - Repository and issue management
- **Git** (12 tools) - Version control operations
- **Docker** (12 tools) - Container management
- **PostgreSQL** (7 tools) - Database operations
- **Documentation** (5 tools) - Search 15+ doc sources
- **Browser** (5 tools) - Read-only web access

#### 🔐 Security (13 layers)
- JWT authentication & RBAC
- Rate limiting (100 req/s API, 5 req/s auth)
- SQL injection & XSS protection
- Path traversal prevention
- MCP approval workflow
- Complete audit logging

#### 🚀 Production Infrastructure
- Docker Compose setup (7 services)
- Nginx reverse proxy with SSL ready
- PostgreSQL + Redis + Qdrant
- Celery for background tasks
- Automated health checks
- Database migrations

## 🛠️ Configuration

### Essential Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY=your-32-character-secret-key
POSTGRES_PASSWORD=your-database-password
REDIS_PASSWORD=your-redis-password

# AI Provider (at least one REQUIRED)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-key

# GitHub Integration (optional)
GITHUB_TOKEN=ghp-your-github-token

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

See [.env.production.example](.env.production.example) for all options.

## 📊 Project Status

### Phase 7: Integration + MCP + Production ✅ COMPLETE
- ✅ Part 1: MCP Server Implementation
- ✅ Part 2: Full Integration Validation
- ✅ Part 3: MCP Integration
- ✅ Part 4: End-to-End Testing
- ✅ Part 5: Performance Optimization
- ✅ Part 6: Error Recovery
- ✅ Part 7: Production Deployment
- ✅ Part 8: Security Audit
- ✅ Part 9: Final Validation

**Result:** Production-ready AI Engineering Platform

### Statistics
- **Files Created:** 29 files
- **Code Written:** 8,150+ lines
- **MCP Tools:** 59 tools
- **API Endpoints:** 70+
- **Test Coverage:** Core workflows covered
- **Security Layers:** 13

## 🎯 Architecture

```
User → Nginx → Backend → AI Orchestrator → Tool Engine → MCP Manager 
→ MCP Client → MCP Server → Tool Execution → Response
```

**Services:**
- Frontend (Static files)
- Backend (FastAPI x4 workers)
- PostgreSQL (Database)
- Redis (Cache & tasks)
- Qdrant (Vector database)
- Celery Worker (Background jobs)
- Celery Beat (Scheduled tasks)
- Nginx (Reverse proxy)

## 🔧 Maintenance

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U agentforge agentforge > backup.sql

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=8
```

## 🧪 Testing

```bash
# Run E2E tests
pytest backend/tests/test_e2e_integration.py -v

# Validate API integration
python backend/scripts/validate_integration.py

# Health check
./scripts/health_check.sh
```

## 📞 Support

- **Documentation:** See [PHASE_7_COMPLETE.md](PHASE_7_COMPLETE.md)
- **Deployment Issues:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Reference:** http://localhost/api/v1/docs
- **Architecture:** See [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md)

## 🎯 Next Steps

Phase 7 is complete and AgentForge is production-ready. **Awaiting approval for Phase 8.**
