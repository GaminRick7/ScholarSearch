#!/usr/bin/env python3
"""
Database setup script for ScholarNet 2.0
"""

import os
import sys
import subprocess
import time
import requests

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Docker is available")
            return True
        else:
            print("Docker is not available")
            return False
    except FileNotFoundError:
        print("Docker is not installed")
        return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Docker Compose is available")
            return True
        else:
            print("Docker Compose is not available")
            return False
    except FileNotFoundError:
        print("Docker Compose is not installed")
        return False

def start_services():
    """Start database services using Docker Compose"""
    print("\nStarting database services...")

    try:
        # Start services in background
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("Services started successfully")

        # Wait for services to be ready
        print("Waiting for services to be ready...")
        time.sleep(10)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to start services: {e}")
        return False

def check_service_health():
    """Check if all services are healthy"""
    print("\nChecking service health...")

    services = {
        'PostgreSQL': 'http://localhost:5432',
        'Redis': 'http://localhost:6379',
        'ChromaDB': 'http://localhost:8001'
    }

    all_healthy = True

    for service_name, url in services.items():
        try:
            if service_name == 'PostgreSQL':
                # PostgreSQL doesn't have HTTP endpoint, check if port is open
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5432))
                sock.close()
                if result == 0:
                    print(f"{service_name} is healthy")
                else:
                    print(f"{service_name} is not responding")
                    all_healthy = False
            elif service_name == 'Redis':
                # Redis doesn't have HTTP endpoint, check if port is open
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 6379))
                sock.close()
                if result == 0:
                    print(f"{service_name} is healthy")
                else:
                    print(f"{service_name} is not responding")
                    all_healthy = False
            else:
                # ChromaDB has HTTP endpoint
                response = requests.get(f"{url}/api/v2/heartbeat", timeout=5)
                if response.status_code == 200:
                    print(f"{service_name} is healthy")
                else:
                    print(f"{service_name} returned status {response.status_code}")
                    all_healthy = False
        except Exception as e:
            print(f"{service_name} health check failed: {e}")
            all_healthy = False

    return all_healthy

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print("\nSetting up Python environment...")

    try:
        # Check if virtual environment exists
        if not os.path.exists('venv'):
            print("Creating virtual environment...")
            subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)

        # Activate virtual environment and install dependencies
        if os.name == 'nt':  # Windows
            pip_cmd = 'venv\\Scripts\\pip'
        else:  # Unix/Linux/macOS
            pip_cmd = 'venv/bin/pip'

        print("Installing Python dependencies...")
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)

        print("Python environment setup completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Python environment setup failed: {e}")
        return False

def initialize_database():
    """Initialize the database with tables and sample data"""
    print("\nInitializing database...")

    try:
        # Run database initialization
        if os.name == 'nt':  # Windows
            python_cmd = 'venv\\Scripts\\python'
        else:  # Unix/Linux/macOS
            python_cmd = 'venv/bin/python'

        subprocess.run([python_cmd, 'src/app/core/init_db.py'], check=True)
        print("Database initialization completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Database initialization failed: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\nCreating environment file...")

    try:
        if not os.path.exists('.env'):
            # Copy env.example to .env
            with open('env.example', 'r') as template:
                content = template.read()

            with open('.env', 'w') as env_file:
                env_file.write(content)

            print("Environment file created (.env)")
        else:
            print("Environment file already exists (.env)")

        return True

    except Exception as e:
        print(f"Failed to create environment file: {e}")
        return False

def main():
    """Main setup function"""
    print("ScholarNet 2.0 Database Setup (Basic Edition)")
    print("=" * 60)

    # Check prerequisites
    if not check_docker():
        print("\nPlease install Docker first: https://docs.docker.com/get-docker/")
        return False

    if not check_docker_compose():
        print("\nPlease install Docker Compose first: https://docs.docker.com/compose/install/")
        return False

    # Create environment file
    if not create_env_file():
        return False

    # Start services
    if not start_services():
        return False

    # Wait a bit more for services to fully start
    print("Waiting for services to fully initialize...")
    time.sleep(15)

    # Check service health
    if not check_service_health():
        print("\nSome services are not healthy. Please check Docker logs:")
        print("  docker-compose logs")
        return False

    # Setup Python environment
    if not setup_python_environment():
        return False

    # Initialize database
    if not initialize_database():
        return False

    print("\nDatabase setup completed successfully!")
    print("\nWhat you now have:")
    print("PostgreSQL database with 5 sample research papers")
    print("ChromaDB service running (empty, ready for hybrid search)")
    print("Redis caching layer for performance")
    print("Database infrastructure ready for hybrid search implementation")

    print("\nNext steps:")
    print("1. Start the backend: python3 src/run.py")
    print("2. Start the frontend: cd visual-search-engine && npm run dev")
    print("3. Open http://localhost:3000 in your browser")
    print("4. Test the API at http://localhost:8000/docs")
    print("5. Check ChromaDB status: GET /api/v1/chromadb/status")

    print("\nNote: ChromaDB is running but not populated with data.")
    print("   It's ready for hybrid search: BM25 + BERT vectors with multi-stage retrieval.")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
