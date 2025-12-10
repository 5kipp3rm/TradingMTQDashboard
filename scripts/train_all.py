"""
Master Training Script
Run all ML training phases in sequence
"""
import os
import sys
import subprocess

def run_phase(script_name, phase_name):
    """Run a training phase script"""
    print(f"\n{'='*70}")
    print(f"  {phase_name}")
    print(f"{'='*70}\n")
    
    result = subprocess.run([sys.executable, f"scripts/{script_name}"], 
                          capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ {phase_name} failed!")
        return False
    
    print(f"\n✅ {phase_name} completed successfully!")
    return True

def main():
    """Run complete ML training pipeline"""
    
    print("\n" + "="*70)
    print("  COMPREHENSIVE ML TRAINING PIPELINE")
    print("="*70)
    print("\nThis will:")
    print("  1. Collect historical data from MT5")
    print("  2. Engineer features from raw data")
    print("  3. Train Random Forest and Ensemble models")
    print("\nEstimated time: 15-30 minutes")
    print("="*70)
    
    response = input("\nProceed with training? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Training cancelled.")
        return
    
    # Phase 1: Data Collection
    if not run_phase("collect_data.py", "PHASE 1: Data Collection"):
        return
    
    # Phase 2: Feature Engineering
    if not run_phase("prepare_features.py", "PHASE 2: Feature Engineering"):
        return
    
    # Phase 3: Model Training
    if not run_phase("train_models.py", "PHASE 3: Model Training"):
        return
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"  🎉 ALL PHASES COMPLETE!")
    print(f"{'='*70}")
    
    print(f"\n📂 Your trained models are in: models/")
    print(f"\nTo use models in your bot:")
    print(f"  1. Open main.py")
    print(f"  2. The ensemble models are automatically loaded")
    print(f"  3. Run: python main.py")
    
    print(f"\n💡 Model recommendations:")
    print(f"  - Ensemble models (highest accuracy)")
    print(f"  - Random Forest models (fastest)")
    
    print(f"\n🚀 Your bot is now AI-powered and ready to trade!")

if __name__ == '__main__':
    main()
