# utils/__init__.py
from .dependency_manager import dependency_manager, get_module, is_available, require_module

__all__ = ['dependency_manager', 'get_module', 'is_available', 'require_module']