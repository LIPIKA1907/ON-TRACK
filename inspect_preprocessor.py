import joblib
import pandas as pd

preprocessor = joblib.load("models/preprocessor.joblib")
print("Preprocessor transformers:")
for name, trans, cols in preprocessor.transformers_:
    print(f"  Transformer '{name}': {type(trans).__name__}")
    if hasattr(trans, "named_steps"):
        for step_name, step in trans.named_steps.items():
            print(f"    Step '{step_name}': {type(step).__name__}")
    print(f"    Columns ({len(cols)}): {cols}")
