@echo off
echo ========================================
echo Starting Neo4j for Bandhan
echo ========================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Check if neo4j container already exists
docker ps -a | findstr neo4j >nul 2>&1
if not errorlevel 1 (
    echo Neo4j container already exists.
    echo Checking status...
    docker ps | findstr neo4j >nul 2>&1
    if not errorlevel 1 (
        echo Neo4j is already running!
    ) else (
        echo Starting existing Neo4j container...
        docker start neo4j
    )
) else (
    echo Creating new Neo4j container...
    docker run --name neo4j ^
      -p 7474:7474 -p 7687:7687 ^
      -e NEO4J_AUTH=neo4j/satarksetu2024 ^
      -d neo4j:latest
)

echo.
echo ========================================
echo Neo4j Status
echo ========================================
docker ps | findstr neo4j

echo.
echo ========================================
echo Connection Details
echo ========================================
echo Web UI: http://localhost:7474
echo Bolt URI: bolt://localhost:7687
echo Username: neo4j
echo Password: satarksetu2024
echo.
echo ========================================
echo Next Steps
echo ========================================
echo 1. Wait 10 seconds for Neo4j to start
echo 2. Run: streamlit run dashboard_enhanced.py
echo 3. Check sidebar for: Graph DB: Neo4j (Connected)
echo.
pause
