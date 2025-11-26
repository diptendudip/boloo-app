#!/usr/bin/env python3
"""
Initialize Monitoring Resources
Populates the database with all resources to be monitored
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.resource_health import (
    ResourceHealth,
    ResourceType,
    ResourceCategory
)


def init_resources():
    """Initialize all monitoring resources"""
    db = SessionLocal()

    try:
        # Define all resources to monitor
        resources_config = [
            # Internal Resources - Infrastructure
            {
                "resource_name": "PostgreSQL Database",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.DATABASE,
                "restart_enabled": True,
                "restart_command": "docker restart boloo-postgres",
                "check_interval_seconds": 60,
                "timeout_seconds": 10,
                "endpoint_url": "postgresql://localhost:5432/boloo",
                "dependencies": ["Network Connectivity"]
            },
            {
                "resource_name": "Redis Cache",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.CACHE,
                "restart_enabled": True,
                "restart_command": "docker restart boloo-redis",
                "check_interval_seconds": 60,
                "timeout_seconds": 10,
                "endpoint_url": "redis://localhost:6379/0",
                "dependencies": ["Network Connectivity"]
            },
            {
                "resource_name": "MinIO Storage",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.STORAGE,
                "restart_enabled": True,
                "restart_command": "docker restart boloo-minio",
                "check_interval_seconds": 60,
                "timeout_seconds": 10,
                "endpoint_url": "http://localhost:9000",
                "dependencies": ["Network Connectivity"]
            },

            # Internal Resources - API Endpoints
            {
                "resource_name": "API: Health Check",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.API,
                "restart_enabled": False,  # API doesn't restart individually
                "restart_command": None,
                "check_interval_seconds": 60,
                "timeout_seconds": 5,
                "endpoint_url": "/health",
                "dependencies": ["PostgreSQL Database", "Redis Cache"]
            },
            {
                "resource_name": "API: Entities",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.API,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 60,
                "timeout_seconds": 10,
                "endpoint_url": "/v1/entities",
                "dependencies": ["PostgreSQL Database", "Redis Cache"]
            },
            {
                "resource_name": "API: Taxonomies",
                "resource_type": ResourceType.INTERNAL,
                "resource_category": ResourceCategory.API,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 60,
                "timeout_seconds": 10,
                "endpoint_url": "/v1/taxonomies",
                "dependencies": ["PostgreSQL Database", "Redis Cache"]
            },

            # External Resources
            {
                "resource_name": "Azure Speech API",
                "resource_type": ResourceType.EXTERNAL,
                "resource_category": ResourceCategory.SPEECH_SERVICE,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 300,  # Check every 5 minutes (less frequent for external)
                "timeout_seconds": 15,
                "endpoint_url": "https://centralindia.api.cognitive.microsoft.com",
                "dependencies": ["Network Connectivity"]
            },
            {
                "resource_name": "Claude AI API",
                "resource_type": ResourceType.EXTERNAL,
                "resource_category": ResourceCategory.AI_SERVICE,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 300,  # Check every 5 minutes
                "timeout_seconds": 15,
                "endpoint_url": "https://api.anthropic.com",
                "dependencies": ["Network Connectivity"]
            },
            {
                "resource_name": "SMTP Email Service",
                "resource_type": ResourceType.EXTERNAL,
                "resource_category": ResourceCategory.EMAIL_SERVICE,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 300,  # Check every 5 minutes
                "timeout_seconds": 15,
                "endpoint_url": "smtp.gmail.com:587",
                "dependencies": ["Network Connectivity"]
            },
            {
                "resource_name": "Network Connectivity",
                "resource_type": ResourceType.EXTERNAL,
                "resource_category": ResourceCategory.NETWORK,
                "restart_enabled": False,
                "restart_command": None,
                "check_interval_seconds": 120,  # Check every 2 minutes
                "timeout_seconds": 10,
                "endpoint_url": "https://www.google.com",
                "dependencies": []
            },
        ]

        created_count = 0
        updated_count = 0

        for config in resources_config:
            # Check if resource already exists
            existing = db.query(ResourceHealth).filter(
                ResourceHealth.resource_name == config["resource_name"]
            ).first()

            if existing:
                # Update existing resource
                for key, value in config.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"✓ Updated: {config['resource_name']}")
            else:
                # Create new resource
                resource = ResourceHealth(**config)
                db.add(resource)
                created_count += 1
                print(f"✓ Created: {config['resource_name']}")

        db.commit()

        print(f"\n{'='*60}")
        print(f"Monitoring Resources Initialized Successfully!")
        print(f"{'='*60}")
        print(f"Created: {created_count} resources")
        print(f"Updated: {updated_count} resources")
        print(f"Total:   {created_count + updated_count} resources")
        print(f"\nResources by type:")

        internal_count = db.query(ResourceHealth).filter(
            ResourceHealth.resource_type == ResourceType.INTERNAL
        ).count()
        external_count = db.query(ResourceHealth).filter(
            ResourceHealth.resource_type == ResourceType.EXTERNAL
        ).count()

        print(f"  Internal: {internal_count}")
        print(f"  External: {external_count}")

        print(f"\nNext steps:")
        print(f"  1. Start Docker services: docker-compose up -d")
        print(f"  2. Start backend server: cd backend && python -m app.main")
        print(f"  3. Trigger initial health check:")
        print(f"     curl -X POST http://localhost:8000/v1/monitoring/health/check")
        print(f"  4. View dashboard:")
        print(f"     curl http://localhost:8000/v1/monitoring/health/dashboard")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error initializing resources: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing monitoring resources...\n")
    init_resources()
