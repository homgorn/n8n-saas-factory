#!/bin/bash
# init.sh - Start development environment for n8n SaaS Factory
# Usage: ./init.sh [--check-only]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting n8n SaaS Factory environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $1 found: $($1 --version 2>/dev/null | head -1)"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

check_port() {
    if lsof -i:"$1" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $1 is in use"
        return 1
    else
        echo -e "${GREEN}✓${NC} Port $1 available"
        return 0
    fi
}

# Check required tools
echo ""
echo "📋 Checking required tools..."
MISSING_TOOLS=0

check_command "node" || MISSING_TOOLS=1
check_command "npm" || MISSING_TOOLS=1
check_command "docker" || MISSING_TOOLS=1
check_command "git" || MISSING_TOOLS=1

# Optional but recommended
check_command "pnpm" || echo "  (pnpm recommended for monorepo)"
check_command "vercel" || echo "  (vercel CLI for deployments)"
check_command "supabase" || echo "  (supabase CLI for local DB)"

if [ "$MISSING_TOOLS" -eq 1 ]; then
    echo -e "${RED}Missing required tools. Please install them first.${NC}"
    exit 1
fi

# Check ports
echo ""
echo "🔌 Checking ports..."
check_port 5678  # n8n
check_port 3000  # Next.js dev
check_port 5432  # Postgres (Supabase)
check_port 6379  # Redis (n8n queue mode)

# Check environment files
echo ""
echo "📄 Checking environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠${NC} .env not found. Copying from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}⚠${NC} Please edit .env with your credentials"
    else
        echo -e "${RED}✗${NC} No .env.example found"
    fi
else
    echo -e "${GREEN}✓${NC} .env exists"
fi

# Start n8n (Docker Compose)
echo ""
echo "🐳 Starting n8n..."
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d n8n
    echo "Waiting for n8n to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:5678/healthz >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} n8n is ready at http://localhost:5678"
            break
        fi
        sleep 2
    done
else
    echo -e "${YELLOW}⚠${NC} No docker-compose.yml found. Starting n8n manually..."
    echo "  Run: npx n8n start"
fi

# Start Supabase local (if available)
if command -v supabase >/dev/null 2>&1 && [ -f "supabase/config.toml" ]; then
    echo ""
    echo "🗄️ Starting Supabase local..."
    supabase start
fi

# Install dependencies for generated SaaS projects
echo ""
echo "📦 Installing dependencies..."
if [ -f "package.json" ]; then
    if command -v pnpm >/dev/null 2>&1; then
        pnpm install --frozen-lockfile
    else
        npm ci
    fi
fi

# Install dependencies for each generated SaaS
for dir in generated-saas/*/; do
    if [ -f "$dir/package.json" ]; then
        echo "  Installing in $dir..."
        (cd "$dir" && npm ci 2>/dev/null || pnpm install 2>/dev/null) &
    fi
done
wait

# Verify n8n workflows directory exists
echo ""
echo "📁 Checking project structure..."
mkdir -p n8n-docs-source
mkdir -p generated-saas
mkdir -p .openchamber/agents
mkdir -p saas-factory/{analyzer,templates,generators}
mkdir -p n8n-wiki/{vector-db,index,metadata,refresh-logs}

# Run database migrations if Supabase is running
if command -v supabase >/dev/null 2>&1 && supabase status 2>/dev/null | grep -q "RUNNING"; then
    echo ""
    echo "🔄 Running database migrations..."
    supabase db reset --linked 2>/dev/null || supabase migration up 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}✅ Environment ready!${NC}"
echo ""
echo "📍 Key URLs:"
echo "  n8n Editor:        http://localhost:5678"
echo "  Next.js Dev:       http://localhost:3000 (run: npm run dev)"
echo "  Supabase Studio:   http://localhost:54323 (if local)"
echo ""
echo "📚 Next steps:"
echo "  1. Open n8n and import workflows from n8n-docs-source/docs/_workflows/"
echo "  2. Run: npm run dev (in generated-saas/<project>/) to start SaaS"
echo "  3. Use OpenChamber to spawn agents: openchamber session create ..."
echo ""

# If check-only flag, exit after checks
if [ "$1" = "--check-only" ]; then
    exit 0
fi