#!/bin/bash

# Prometheus Setup Script for AI Copilot
# This script sets up a local Prometheus instance for testing

echo "🚀 Setting up Prometheus for AI Copilot testing..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Install Prometheus
echo "📦 Installing Prometheus..."
brew install prometheus

# Install Node Exporter
echo "📦 Installing Node Exporter..."
brew install node_exporter

# Create Prometheus configuration directory
PROMETHEUS_DIR="$HOME/.prometheus"
mkdir -p "$PROMETHEUS_DIR"

# Create prometheus.yml configuration
echo "⚙️  Creating Prometheus configuration..."
cat > "$PROMETHEUS_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'ai-copilot'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF

echo "✅ Prometheus configuration created at $PROMETHEUS_DIR/prometheus.yml"

# Create startup script
echo "📝 Creating startup script..."
cat > "$PROMETHEUS_DIR/start_prometheus.sh" << 'EOF'
#!/bin/bash

echo "🚀 Starting Prometheus services..."

# Start Node Exporter in background
echo "📊 Starting Node Exporter on port 9100..."
node_exporter &
NODE_EXPORTER_PID=$!

# Wait a moment for Node Exporter to start
sleep 2

# Start Prometheus
echo "📈 Starting Prometheus on port 9090..."
prometheus --config.file="$HOME/.prometheus/prometheus.yml" --storage.tsdb.path="$HOME/.prometheus/data" --web.console.libraries="$HOME/.prometheus/console_libraries" --web.console.templates="$HOME/.prometheus/consoles" --web.enable-lifecycle

# Cleanup function
cleanup() {
    echo "🛑 Stopping services..."
    kill $NODE_EXPORTER_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for services
wait
EOF

chmod +x "$PROMETHEUS_DIR/start_prometheus.sh"

# Create stop script
cat > "$PROMETHEUS_DIR/stop_prometheus.sh" << 'EOF'
#!/bin/bash

echo "🛑 Stopping Prometheus services..."

# Kill Node Exporter
pkill -f node_exporter

# Kill Prometheus
pkill -f prometheus

echo "✅ All services stopped"
EOF

chmod +x "$PROMETHEUS_DIR/stop_prometheus.sh"

echo ""
echo "🎉 Prometheus setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start Prometheus: $PROMETHEUS_DIR/start_prometheus.sh"
echo "2. Access Prometheus UI: http://localhost:9090"
echo "3. Access Node Exporter metrics: http://localhost:9100/metrics"
echo "4. Run the test: python test_prometheus.py"
echo "5. Stop services: $PROMETHEUS_DIR/stop_prometheus.sh"
echo ""
echo "🔍 Useful Prometheus queries to try:"
echo "   - up (service availability)"
echo "   - node_cpu_seconds_total (CPU metrics)"
echo "   - node_memory_MemAvailable_bytes (memory metrics)"
echo "   - rate(node_cpu_seconds_total[5m]) (CPU usage rate)"
echo ""
echo "📚 For more information, see: https://prometheus.io/docs/"
