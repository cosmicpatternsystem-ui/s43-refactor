# S43 AI Safety Guards

Critical flags:
- AUTONOMOUS_AI
- WALLET_{slot}_AUTONOMOUS_AI
- AI_TRADER_ENABLE
- OPENAI_TRADE_ENABLE

Safe defaults:
- AUTONOMOUS_AI=0
- OPENAI_TRADE_ENABLE=0

Important rule:
- READY_FOR_AUTONOMOUS_DECISION is not permission for live autonomous trading.

Review before activation:
- RiskDecision.assess
- PhoenixDecision
- AITrader
- _ai_trader
- OPENAI_TRADE_ENABLE checks
- AUTONOMOUS_AI checks
- wallet-level autonomous flags
- final trade execution path

Current position:
- Autonomous/live trading must remain disabled until decision and execution guards are reviewed.