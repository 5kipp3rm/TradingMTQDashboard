"""
Python 3.14 Compatibility Patch
Fixes contextlib._GeneratorContextManager missing 'throw' method
This is required for FastAPI dependency injection in Python 3.14
"""
import sys
from contextlib import _GeneratorContextManager


if sys.version_info >= (3, 14):
    # Python 3.14 removed several methods from _GeneratorContextManager
    # We need to restore them for FastAPI compatibility

    if not hasattr(_GeneratorContextManager, 'throw'):
        def _throw(self, typ, val=None, tb=None):
            """Throw an exception into the generator."""
            if typ is None:
                return next(self.gen)

            if val is None:
                if tb is None:
                    raise typ
                val = typ()
            if tb is not None:
                val = val.with_traceback(tb)

            try:
                return self.gen.throw(typ, val, tb)
            except StopIteration as exc:
                return exc.value

        _GeneratorContextManager.throw = _throw

    if not hasattr(_GeneratorContextManager, '__iter__'):
        def _iter(self):
            """Return the generator iterator."""
            return self.gen

        _GeneratorContextManager.__iter__ = _iter

    if not hasattr(_GeneratorContextManager, '__next__'):
        def _next(self):
            """Return the next value from the generator."""
            return next(self.gen)

        _GeneratorContextManager.__next__ = _next

    print("✅ Applied Python 3.14 compatibility patch for contextlib")
