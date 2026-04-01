from app.agents.base import BaseAgent
print('initial', BaseAgent._otel_initialized)
for i in range(5):
    print('---- inst', i, 'before', BaseAgent._otel_initialized)
    BaseAgent()
    print('after', BaseAgent._otel_initialized)
