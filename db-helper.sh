#!/bin/bash

# Database Management Helper Script

echo "🗄️ PostgreSQL Container Management"
echo ""

show_status() {
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "northwind-postgres"; then
        echo "✅ northwind-postgres is RUNNING"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep northwind-postgres
    elif docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "northwind-postgres"; then
        echo "🛑 northwind-postgres is STOPPED"
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep northwind-postgres
    else
        echo "❌ northwind-postgres container NOT FOUND"
    fi
    echo ""
}

case "$1" in
    "status"|"")
        show_status
        ;;
    "start")
        if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "✅ northwind-postgres is already running"
        elif docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "🔄 Starting northwind-postgres..."
            docker start northwind-postgres
            echo "✅ Started"
        else
            echo "❌ Container not found. Use './db-helper.sh create' to create it."
        fi
        ;;
    "stop")
        if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "🛑 Stopping northwind-postgres..."
            docker stop northwind-postgres
            echo "✅ Stopped"
        else
            echo "⚠️  northwind-postgres is not running"
        fi
        ;;
    "create")
        if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "⚠️  northwind-postgres container already exists"
            show_status
        else
            echo "🚀 Creating new northwind-postgres container..."
            docker run -d \
                --name northwind-postgres \
                -e POSTGRES_DB=northwind \
                -e POSTGRES_USER=postgres \
                -e POSTGRES_PASSWORD=password \
                -p 5432:5432 \
                -v "$(pwd)/postgre/northwind.sql:/docker-entrypoint-initdb.d/northwind.sql" \
                postgres:15
            echo "✅ Container created and starting..."
        fi
        ;;
    "remove")
        if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "🛑 Stopping northwind-postgres..."
            docker stop northwind-postgres
        fi
        if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            echo "🗑️  Removing northwind-postgres container..."
            docker rm northwind-postgres
            echo "✅ Container removed"
        else
            echo "⚠️  northwind-postgres container not found"
        fi
        ;;
    "logs")
        if docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
            docker logs northwind-postgres
        else
            echo "❌ northwind-postgres container not found"
        fi
        ;;
    "help")
        echo "Usage: ./db-helper.sh [command]"
        echo ""
        echo "Commands:"
        echo "  status    Show container status (default)"
        echo "  start     Start the container"
        echo "  stop      Stop the container"
        echo "  create    Create new container with Northwind data"
        echo "  remove    Stop and remove the container"
        echo "  logs      Show container logs"
        echo "  help      Show this help message"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use './db-helper.sh help' for available commands"
        ;;
esac
