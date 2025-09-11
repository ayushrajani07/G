#!/bin/bash
# G6 Analytics Platform - Setup Script

echo "🚀 Setting up G6 Analytics Platform..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run first-time diagnostics
echo "🔧 Running first-time diagnostics..."
python first_run_diagnostics.py

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ Creating .env template file..."
    cat > .env << EOF
# Kite Connect API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Optional: InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=your_org_here
EOF
    echo "📝 Please edit .env file with your API credentials"
fi

echo "✅ Setup complete! Run 'python main.py' to start the platform."
