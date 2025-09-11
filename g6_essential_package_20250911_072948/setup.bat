@echo off
REM G6 Analytics Platform - Windows Setup Script

echo 🚀 Setting up G6 Analytics Platform...

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Run first-time diagnostics
echo 🔧 Running first-time diagnostics...
python first_run_diagnostics.py

REM Check if .env file exists
if not exist .env (
    echo ⚠️ Creating .env template file...
    (
    echo # Kite Connect API Credentials
    echo KITE_API_KEY=your_api_key_here
    echo KITE_API_SECRET=your_api_secret_here
    echo KITE_ACCESS_TOKEN=your_access_token_here
    echo.
    echo # Optional: InfluxDB Configuration
    echo INFLUXDB_URL=http://localhost:8086
    echo INFLUXDB_TOKEN=your_token_here
    echo INFLUXDB_ORG=your_org_here
    ) > .env
    echo 📝 Please edit .env file with your API credentials
)

echo ✅ Setup complete! Run 'python main.py' to start the platform.
pause
