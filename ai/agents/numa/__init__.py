# ai/agents/numa/__init__.py
"""
Numa multi-agent reasoning system (moved from pcd/Numa).
Public interface for calling the reasoning pipeline.
"""
from .main import analyze_user

__all__ = ["analyze_user"]