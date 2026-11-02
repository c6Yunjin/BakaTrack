# Central settings. Every module imports from here.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "bakatrack.db")

CONFIDENCE_THRESHOLD = 0.60   # below this, the bot shows the referral message
RANDOM_SEED = 42              # fixed so training results are reproducible

# Step 3: intent classifier paths and settings
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents.json")
MODEL_PATH = os.path.join(BASE_DIR, "models", "intent_model.joblib")
EVIDENCE_DIR = os.path.join(BASE_DIR, "training", "evidence")
TEST_SIZE = 0.20              # 20% of sentences are hidden for the "exam"
