"""ProPlan ABI backend application package.

`app.services` holds the staged semantic-extraction pipeline:

    crawl -> clean -> markdown -> classify -> rule extract -> llm extract
          -> normalize -> confidence -> merge profile -> ABI evidence

The LLM is one component inside a structured system, not the engine itself.
"""
