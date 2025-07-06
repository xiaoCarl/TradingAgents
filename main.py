from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "ollama"  # Use a different model
config["backend_url"] = "http://localhost:11434/v1"  # Use a different backend
config["deep_think_llm"] = "llama3-groq-tool-use:8b"  # Use a different model
config["quick_think_llm"] = "llama3-groq-tool-use:8b"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Increase debate rounds

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
