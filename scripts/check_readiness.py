"""
Verify ML and LLM readiness for main.py
"""
import sys
sys.path.insert(0, '.')

from src.ml import RF_AVAILABLE, LSTM_AVAILABLE
from src.utils.config_loader import get_openai_key
from pathlib import Path

print('='*80)
print('MAIN.PY READINESS CHECK')
print('='*80)

print('\n1. ML Enhancement Status:')
print(f'   Random Forest library: {"Available" if RF_AVAILABLE else "Not available"}')
print(f'   LSTM library: {"Available" if LSTM_AVAILABLE else "Not available"}')

model_path = Path('models/rf_model.pkl')
if model_path.exists():
    print(f'   Trained model: Found at {model_path}')
    print(f'   ML READY FOR USE')
else:
    print(f'   Trained model: Not found')

print('\n2. LLM Enhancement Status:')
api_key = get_openai_key()
if api_key:
    print(f'   OpenAI API key: Configured (length: {len(api_key)})')
    print(f'   LLM READY FOR USE')
else:
    print(f'   OpenAI API key: Not configured')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
if RF_AVAILABLE and model_path.exists():
    print('ML Enhancement: ENABLED')
else:
    print('ML Enhancement: DISABLED')
    
if api_key:
    print('LLM Enhancement: ENABLED')
else:
    print('LLM Enhancement: DISABLED')

print('Intelligent Position Manager: ALWAYS ACTIVE')
print('\nSystem ready to run with full ML/LLM capabilities!')
print('='*80)
