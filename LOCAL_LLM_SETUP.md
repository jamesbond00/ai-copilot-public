# Local LLM Setup Guide

This guide shows you how to set up and use local LLMs with your AI Copilot system, eliminating the need for OpenAI API billing while maintaining full functionality.

## 🚀 Quick Start

### 1. Install Ollama

```bash
# macOS (using Homebrew)
brew install ollama

# Start the Ollama service
brew services start ollama
```

### 2. Download Models

```bash
# Download a lightweight model (recommended for 18GB RAM)
ollama pull qwen2:1.5b

# Or download a larger model if you have more RAM
ollama pull llama3:8b
```

### 3. Test the Setup

```bash
# Run the comprehensive test suite
python test_local_llm.py

# Or run the simple demo
python src/llm/hello_llm_local.py
```

## 📋 System Requirements

- **RAM**: 18GB+ recommended for Qwen-1.5B, 32GB+ for LLaMA-3-8B
- **Storage**: ~1GB for Qwen-1.5B, ~5GB for LLaMA-3-8B
- **OS**: macOS, Linux, or Windows

## 🔧 Configuration

### Environment Variables

You can configure the system using environment variables:

```bash
# Set preferred provider (local, openai, or hybrid)
export AI_COPILOT_PROVIDER=local

# Set local model
export AI_COPILOT_LOCAL_MODEL=qwen2:1.5b

# Set Ollama host (default: http://localhost:11434)
export OLLAMA_HOST=http://localhost:11434

# Optional: Set OpenAI API key for hybrid mode
export OPENAI_API_KEY=your_openai_key_here
```

### Configuration File

The system automatically creates a configuration file at `~/.ai-copilot/config.yaml`:

```yaml
preferred_provider: local
fallback_provider: openai
local_model: qwen2:1.5b
openai_model: gpt-3.5-turbo
ollama_host: http://localhost:11434
enable_hybrid: true
```

## 🎯 Usage Examples

### Basic Local Analysis

```python
from src.llm.local_analyzer import LocalLogAnalyzer
from src.data.fetchers import LogEntry
from datetime import datetime, timedelta

# Create analyzer
analyzer = LocalLogAnalyzer(model="qwen2:1.5b")

# Create sample logs
logs = [
    LogEntry(
        timestamp=datetime.now() - timedelta(hours=1),
        level="ERROR",
        source="web-server",
        message="Database connection timeout",
        metadata={"timeout": 30}
    )
]

# Analyze logs
result = analyzer.analyze_logs(logs, "daily_summary")
print(f"Summary: {result.summary}")
```

### Hybrid Mode (Local + OpenAI)

```python
from src.llm.local_analyzer import HybridLogAnalyzer

# Create hybrid analyzer (prefers local, falls back to OpenAI)
analyzer = HybridLogAnalyzer(
    openai_api_key="your_key_here",
    prefer_local=True
)

# Use the same interface
result = analyzer.analyze_logs(logs, "error_analysis")
```

### Factory Pattern

```python
from src.llm.copilot import create_analyzer, create_copilot_service

# Auto-select best available analyzer
analyzer = create_analyzer()  # Uses local if available, otherwise OpenAI

# Create full copilot service
class MockFetcher:
    def fetch_logs(self, start_time, end_time):
        return your_logs_here

service = create_copilot_service(MockFetcher(), provider="local")
result = service.get_daily_summary()
```

## 📊 Available Models

### Local Models (via Ollama)

| Model | Size | RAM Required | Speed | Quality |
|-------|------|--------------|-------|---------|
| `qwen2:1.5b` | ~1GB | 8GB+ | Fast | Good |
| `qwen2:3b` | ~2GB | 12GB+ | Medium | Better |
| `llama3:8b` | ~5GB | 16GB+ | Medium | Excellent |
| `llama3:70b` | ~40GB | 64GB+ | Slow | Best |

### Download Commands

```bash
# Lightweight models
ollama pull qwen2:1.5b
ollama pull qwen2:3b

# Medium models
ollama pull llama3:8b
ollama pull mistral:7b

# Large models (if you have enough RAM)
ollama pull llama3:70b
ollama pull codellama:34b
```

## 🔄 Analysis Types

The system supports different types of log analysis:

- **`daily_summary`**: Overview of system health and key issues
- **`error_analysis`**: Focus on errors and failures
- **`performance_analysis`**: Performance bottlenecks and optimization

```python
# Different analysis types
daily_result = analyzer.analyze_logs(logs, "daily_summary")
error_result = analyzer.analyze_logs(logs, "error_analysis")
perf_result = analyzer.analyze_logs(logs, "performance_analysis")
```

## 🛠️ Troubleshooting

### Common Issues

1. **"No models available"**
   ```bash
   # Check if Ollama is running
   brew services list | grep ollama
   
   # Start Ollama if needed
   brew services start ollama
   
   # List available models
   ollama list
   ```

2. **"Model not found"**
   ```bash
   # Download the model
   ollama pull qwen2:1.5b
   
   # Verify installation
   ollama list
   ```

3. **"Connection refused"**
   ```bash
   # Check if Ollama is running on correct port
   curl http://localhost:11434/api/tags
   
   # Restart Ollama service
   brew services restart ollama
   ```

4. **Out of memory errors**
   - Use a smaller model: `qwen2:1.5b` instead of `llama3:8b`
   - Close other applications to free up RAM
   - Consider using a model with quantization

### Performance Optimization

1. **Use quantized models** (smaller, faster):
   ```bash
   ollama pull qwen2:1.5b-q4_0  # 4-bit quantization
   ```

2. **Adjust Ollama settings**:
   ```bash
   # Set environment variables for better performance
   export OLLAMA_FLASH_ATTENTION=1
   export OLLAMA_KV_CACHE_TYPE=q8_0
   ```

3. **Monitor resource usage**:
   ```bash
   # Check Ollama memory usage
   ps aux | grep ollama
   
   # Monitor system resources
   htop
   ```

## 🔒 Security & Privacy

### Benefits of Local LLMs

- **No data sent to external services**: All processing happens locally
- **No API costs**: No per-token billing
- **Offline capability**: Works without internet connection
- **Data privacy**: Logs never leave your machine

### Best Practices

1. **Keep models updated**:
   ```bash
   ollama pull qwen2:1.5b  # Updates to latest version
   ```

2. **Monitor disk usage**:
   ```bash
   # Check model storage
   du -sh ~/.ollama/models
   ```

3. **Use appropriate models**: Don't use unnecessarily large models for simple tasks

## 📈 Performance Comparison

| Provider | Speed | Cost | Privacy | Quality |
|----------|-------|------|---------|---------|
| Local (Qwen-1.5B) | Fast | Free | High | Good |
| Local (LLaMA-3-8B) | Medium | Free | High | Excellent |
| OpenAI GPT-3.5 | Fast | $ | Low | Excellent |
| OpenAI GPT-4 | Medium | $$ | Low | Best |

## 🎉 Next Steps

1. **Integrate with your existing workflow**: Update your code to use `create_analyzer()` instead of hardcoded OpenAI calls
2. **Experiment with different models**: Try various models to find the best balance of speed and quality
3. **Set up monitoring**: Monitor your local LLM performance and resource usage
4. **Consider hybrid mode**: Use local models for most tasks, OpenAI for complex analysis

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Model Library](https://ollama.ai/library)
- [Performance Benchmarks](https://ollama.ai/library/qwen2:1.5b)
- [Community Models](https://huggingface.co/models)

---

**Happy analyzing! 🚀** Your local LLM setup is now ready to provide cost-effective, private log analysis without any external API dependencies.
