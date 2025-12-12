from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
MODEL_DIR = Path(__file__).resolve().parent / "qgen_model" / "flan_t5_qgen_ep6_clean"
print("MODEL_DIR:", MODEL_DIR)
tok = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
print("tokenizer OK")
model = AutoModelForSeq2SeqLM.from_pretrained(str(MODEL_DIR), local_files_only=True)
print("model OK")
