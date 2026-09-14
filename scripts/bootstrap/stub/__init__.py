"""A local stand-in for OpenRouter, so the bootstrap can be exercised for free.

``python -m scripts.bootstrap.stub --port N`` serves the two endpoints the
stack calls: ``/embeddings`` answers with deterministic unit vectors of the
real model's width, and ``/chat/completions`` answers ``400`` so every agent
takes the deterministic fallback it already has for a failed call. Nothing
here resembles a measurement — it exists to prove the plumbing, not the audit.
"""
