"""
Base Model Interface

All AI models inherit from this base class for consistency
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Model metadata"""

    name: str
    version: str
    loaded: bool
    device: str  # 'cpu', 'mps', 'cuda'
    memory_usage_mb: Optional[float] = None


class BaseModel(ABC):
    """Base class for all AI models"""

    def __init__(self):
        self._loaded = False
        self._model: Optional[Any] = None

    @abstractmethod
    async def load(self) -> None:
        """Load model weights and initialize"""
        pass

    @abstractmethod
    async def unload(self) -> None:
        """Unload model to free memory"""
        pass

    @abstractmethod
    def get_info(self) -> ModelInfo:
        """Get model information"""
        pass

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._loaded
