import pandas as pd
import json
import random


# Paths
INPUT_EXCEL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\pruned_training_data_relaxed_fixed.xlsx"
TRAIN_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\train.jsonl"
VAL_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\val.jsonl"

SYSTEM_PROMPT = """You are an expert medical AI assistant specialized in analyzing ultrasound reports. 
Your task is to extract information about gallstones and format it strictly as a JSON object.

Extraction Rules:
1. 'gallstone_found': boolean. Set to true if gallstones are present. Set to false if completely absent or negated (e.g., 'no stone').
2. 'size_min': float. The minimum size of a single stone. Set to null if not specified.
3. 'size_max': float. The maximum size of a single stone. Set to null if not specified. DO NOT put summation size or gallbladder size here.
4. 'size_summation': float. The total size burden of multiple stones combined (usually indicated by 'in summation'). Set to null if not specified.
5. 'unit': string. The unit of measurement ('cm' or 'mm'). Set to null if no sizes are found.

Output ONLY the JSON object. Do not include markdown formatting or explanations."""

def create_message(row):
    # Input text
    user_text = str(row['relaxed_pruned_report'])
    
    # Target JSON
    target_json = {
        "gallstone_found": bool(row['gallstone_found']) if pd.notna(row['gallstone_found']) else False,
        "size_min": float(row['gallstone_size_min']) if pd.notna(row['gallstone_size_min']) else None,
        "size_max": float(row['gallstone_size_max']) if pd.notna(row['gallstone_size_max']) else None,
        "size_summation": float(row['gallstone_size_summation']) if pd.notna(row['gallstone_size_summation']) else None,
        "unit": str(row['gallstone_size_unit']) if pd.notna(row['gallstone_size_unit']) else None
    }
    
    # Format as ChatML
    message = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract gallstone information from this report:\n\n{user_text}"},
            {"role": "assistant", "content": json.dumps(target_json, ensure_ascii=False)}
        ]
    }
    return message

def main():
    print(f"Loading data from {INPUT_EXCEL}...")
    df = pd.read_excel(INPUT_EXCEL)
    
    # Generate messages
    messages = df.apply(create_message, axis=1).tolist()
    
    # Split 85/15 (Shuffle first)
    random.seed(42)
    random.shuffle(messages)
    split_idx = int(len(messages) * 0.85)
    train_msgs = messages[:split_idx]
    val_msgs = messages[split_idx:]
    
    # Save Train
    with open(TRAIN_JSONL, 'w', encoding='utf-8') as f:
        for m in train_msgs:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
            
    # Save Val
    with open(VAL_JSONL, 'w', encoding='utf-8') as f:
        for m in val_msgs:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
            
    print(f"Successfully generated datasets!")
    print(f"Train samples: {len(train_msgs)}")
    print(f"Validation samples: {len(val_msgs)}")
    print(f"Saved to:\n - {TRAIN_JSONL}\n - {VAL_JSONL}")

if __name__ == "__main__":
    main()
