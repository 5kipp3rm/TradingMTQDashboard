"""
Base Indicator Class
Abstract base for all technical indicators
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """Result from indicator calculation"""
    values: np.ndarray
    signals: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseIndicator(ABC):
    """
    Abstract base class for technical indicators
    
    All indicators should inherit from this class and implement
    the calculate() method.
    """
    
    def __init__(self, name: str):
        """
        Initialize indicator
        
        Args:
            name: Indicator name
        """
        self.name = name
    
    @abstractmethod
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate indicator values
        
        Args:
            data: Price data (close prices typically)
            **kwargs: Additional parameters
            
        Returns:
            IndicatorResult with calculated values
        """
        pass
    
    def validate_data(self, data: np.ndarray, min_length: int) -> bool:
        """
        Validate input data
        
        Args:
            data: Input data
            min_length: Minimum required length
            
        Returns:
            True if valid, False otherwise
        """
        if data is None or len(data) < min_length:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
