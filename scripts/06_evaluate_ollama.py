import json
import requests
import time
import pandas as pd
from tqdm import tqdm
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

VAL_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\val.jsonl"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "medgemma-gallstone"

def get_ollama_response(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0 # ไม่สุ่มเดา เอาคำตอบที่มั่นใจที่สุด
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"\nError calling Ollama: {e}")
        return "{}"

def main():
    print("กำลังโหลดข้อสอบ (Validation Set)...")
    with open(VAL_JSONL, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    records = []
    
    print(f"เริ่มทำข้อสอบทั้งหมด {len(lines)} ข้อ ผ่าน Ollama...")
    start_time = time.time()
    
    for line in tqdm(lines, desc="AI กำลังทำข้อสอบ"):
        data = json.loads(line)
        messages = data["messages"]
        
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        truth_msg = next(m["content"] for m in messages if m["role"] == "assistant")
        
        # 1. ให้ Ollama ทำนาย
        pred_text = get_ollama_response(user_msg)
        
        # 2. แปลงข้อความกลับเป็น Dictionary
        try:
            truth_json = json.loads(truth_msg)
        except:
            truth_json = {"gallstone_found": False}
            
        try:
            # ตัดข้อความส่วนเกินที่อาจจะติดมา เอาแค่ในวงเล็บปีกกา
            start_idx = pred_text.find('{')
            end_idx = pred_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                clean_pred = pred_text[start_idx:end_idx+1]
                pred_json = json.loads(clean_pred)
            else:
                pred_json = json.loads(pred_text)
        except:
            pred_json = {"gallstone_found": False, "_error": "Invalid JSON"}

        # 3. ดึงค่าจริง vs ทายผล
        truth_found = truth_json.get("gallstone_found", False)
        pred_found = pred_json.get("gallstone_found", False)
        
        records.append({
            "Prompt": user_msg,
            "Truth_Found": truth_found,
            "Pred_Found": pred_found,
            "Truth_JSON": truth_msg,
            "Pred_JSON": pred_text
        })
        
    end_time = time.time()
    df = pd.DataFrame(records)
    
    # --- คำนวณผลลัพธ์ความแม่นยำ ---
    print("\n" + "="*50)
    print("📊 รายงานผลความแม่นยำ (Detailed Evaluation Report)")
    print("="*50)
    
    y_true = df["Truth_Found"].astype(bool)
    y_pred = df["Pred_Found"].astype(bool)
    
    acc = accuracy_score(y_true, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    print(f"เวลาที่ใช้ทั้งหมด: {(end_time - start_time) / 60:.1f} นาที")
    print(f"ทำข้อสอบไปทั้งหมด: {len(df)} ข้อ")
    print(f"✅ ความแม่นยำรวม (Accuracy): {acc*100:.2f}%")
    print(f"🔍 ความไว (Sensitivity/Recall - เจอโรคทายว่าเจอ): {sensitivity*100:.2f}%")
    print(f"🛡️ ความจำเพาะ (Specificity - ไม่เจอโรคทายว่าไม่เจอ): {specificity*100:.2f}%")
    print("\nรายละเอียด:")
    print(f"- ทายถูกว่า 'มีนิ่ว' (True Positive): {tp} เคส")
    print(f"- ทายถูกว่า 'ไม่มีนิ่ว' (True Negative): {tn} เคส")
    print(f"- ❌ พลาดทายว่า 'มี' ทั้งที่ 'ไม่มี' (False Positive / ทายเว่อร์): {fp} เคส")
    print(f"- ❌ พลาดทายว่า 'ไม่มี' ทั้งที่ 'มี' (False Negative / หลุด): {fn} เคส")
    
    # Save Error cases for review
    errors_df = df[df["Truth_Found"] != df["Pred_Found"]]
    error_file = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\evaluation_errors.xlsx"
    errors_df.to_excel(error_file, index=False)
    
    print("\n" + "="*50)
    if len(errors_df) > 0:
        print(f"📝 เคสที่ AI ทายผิด ({len(errors_df)} เคส) ถูกเซฟไว้ให้คุณหมอรีวิวที่:")
        print(error_file)
    else:
        print("🎉 สุดยอด! AI ทายถูก 100% ไม่มีข้อผิดพลาดเลยครับ!")
    print("="*50)

if __name__ == "__main__":
    main()
