#!/bin/bash

# Database & Cache Management Helper Script

echo "🗄️ PostgreSQL & Redis Container Management"
echo ""

show_status() {
    echo "📊 Container Status:"
    echo ""
    
    # Check PostgreSQL
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "northwind-postgres"; then
        echo "✅ PostgreSQL (northwind-postgres) is RUNNING"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep northwind-postgres
    elif docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "northwind-postgres"; then
        echo "🛑 PostgreSQL (northwind-postgres) is STOPPED"
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep northwind-postgres
    else
        echo "❌ PostgreSQL (northwind-postgres) container NOT FOUND"
    fi
    
    # Check Redis
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "redis-stack"; then
        echo "✅ Redis (redis-stack) is RUNNING"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep redis-stack
    elif docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "redis-stack"; then
        echo "🛑 Redis (redis-stack) is STOPPED"
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep redis-stack
    else
        echo "❌ Redis (redis-stack) container NOT FOUND"
    fi
    echo ""
}

case "$1" in
    "status"|"")
        show_status
        ;;
    "start")
        container_name="${2:-all}"
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "✅ PostgreSQL is already running"
            elif docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "🔄 Starting PostgreSQL (northwind-postgres)..."
                docker start northwind-postgres
                echo "✅ PostgreSQL Started"
            else
                echo "❌ PostgreSQL container not found. Use './db-helper.sh create postgres' to create it."
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "✅ Redis is already running"
            elif docker ps -a --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "🔄 Starting Redis (redis-stack)..."
                docker start redis-stack
                echo "✅ Redis Started"
            else
                echo "❌ Redis container not found. Use './db-helper.sh create redis' to create it."
            fi
        fi
        ;;
    "stop")
        container_name="${2:-all}"
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "🛑 Stopping PostgreSQL (northwind-postgres)..."
                docker stop northwind-postgres
                echo "✅ PostgreSQL Stopped"
            else
                echo "⚠️  PostgreSQL is not running"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "🛑 Stopping Redis (redis-stack)..."
                docker stop redis-stack
                echo "✅ Redis Stopped"
            else
                echo "⚠️  Redis is not running"
            fi
        fi
        ;;
    "create")
        container_name="${2:-all}"
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "⚠️  PostgreSQL container already exists"
            else
                echo "🚀 Creating new PostgreSQL container (northwind-postgres)..."
                docker run -d \
                    --name northwind-postgres \
                    -e POSTGRES_DB=northwind \
                    -e POSTGRES_USER=postgres \
                    -e POSTGRES_PASSWORD=password \
                    -p 5432:5432 \
                    postgres:15
                echo "⏳ Waiting for PostgreSQL to initialize..."
                sleep 10

                echo "📥 Downloading Northwind SQL dump..."
                curl -s -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql

                echo "🔄 Importing data into Northwind database..."
                docker cp northwind.sql northwind-postgres:/northwind.sql
                docker exec northwind-postgres psql -U postgres -d northwind -f /northwind.sql
                rm northwind.sql

                echo "✅ Northwind database ready (localhost:5432, DB: northwind, User: postgres, Password: password)"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "⚠️  Redis container already exists"
            else
                echo "🚀 Creating new Redis container (redis-stack)..."
                docker run -d \
                    --name redis-stack \
                    -p 6379:6379 \
                    -p 8001:8001 \
                    redis/redis-stack:latest
                echo "✅ Redis container created and starting..."
            fi
        fi
        show_status
        ;;
    "remove")
        container_name="${2:-all}"
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "🛑 Stopping PostgreSQL (northwind-postgres)..."
                docker stop northwind-postgres
            fi
            if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "🗑️  Removing PostgreSQL container..."
                docker rm northwind-postgres
                echo "✅ PostgreSQL container removed"
            else
                echo "⚠️  PostgreSQL container not found"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "🛑 Stopping Redis (redis-stack)..."
                docker stop redis-stack
            fi
            if docker ps -a --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "🗑️  Removing Redis container..."
                docker rm redis-stack
                echo "✅ Redis container removed"
            else
                echo "⚠️  Redis container not found"
            fi
        fi
        ;;
    "logs")
        container_name="${2:-postgres}"
        if [ "$container_name" = "postgres" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
                echo "📋 PostgreSQL logs:"
                docker logs northwind-postgres
            else
                echo "❌ PostgreSQL container not found"
            fi
        elif [ "$container_name" = "redis" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "redis-stack"; then
                echo "📋 Redis logs:"
                docker logs redis-stack
            else
                echo "❌ Redis container not found"
            fi
        fi
        ;;
    "help")
        echo "Usage: ./db-helper.sh [command] [container]"
        echo ""
        echo "Commands:"
        echo "  status              Show all container status (default)"
        echo "  start [container]   Start container(s) [all|postgres|redis] (default: all)"
        echo "  stop [container]    Stop container(s) [all|postgres|redis] (default: all)"
        echo "  create [container]  Create new container(s) [all|postgres|redis] (default: all)"
        echo "  remove [container]  Stop and remove container(s) [all|postgres|redis] (default: all)"
        echo "  logs [container]    Show container logs [postgres|redis] (default: postgres)"
        echo "  help                Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./db-helper.sh start redis     # Start only Redis"
        echo "  ./db-helper.sh stop postgres   # Stop only PostgreSQL"
        echo "  ./db-helper.sh create all       # Create both containers"
        echo "  ./db-helper.sh logs redis       # Show Redis logs"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use './db-helper.sh help' for available commands"
        ;;
esac
