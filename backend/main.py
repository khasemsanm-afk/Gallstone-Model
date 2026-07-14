import re
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Gallstone AI Extraction API", version="1.0")

# ชี้ไปที่ Ollama ผ่าน localhost โดยตรง (สำหรับรันแบบ Host Mode บน Linux)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "medgemma-gallstone"

class PatientData(BaseModel):
    raw_text: str

# อัลกอริทึมตัดคำ (แบบเดียวกับ Data Training)
GB_KEYWORDS = re.compile(r"\b(gallbladder|gall\s*bladder|gb|gall\s*stones?|gallstones?|gb\s*stones?|cholelithiasis|calculi|calculus|gs|stones?|biliary|cystic\s+duct|bile\s+ducts?|cbd|ihd|cholecyst\w*|polyps?|sludges?)\b", re.IGNORECASE)

def clean_medical_text(report: str) -> str:
    report = str(report) if report else ""
    if not report.strip():
        return ""
        
    impression_match = re.search(r"\b(?:impression|opinion|conclusion)[\s:;\.-]*(.*)", report, re.IGNORECASE | re.DOTALL)
    if impression_match:
        imp_text = impression_match.group(1)
        finding_text = report[:impression_match.start()]
    else:
        imp_text = ""
        finding_text = report
        
    def extract_gb_paragraphs(text: str) -> str:
        lines = text.replace("\r\n", "\n").split("\n")
        kept_lines = []
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            if GB_KEYWORDS.search(line_clean):
                line_clean = re.sub(r"\s+", " ", line_clean)
                kept_lines.append(line_clean.lower())
        return " ".join(kept_lines)

    parts = []
    
    f_finding = extract_gb_paragraphs(finding_text)
    if f_finding:
        parts.append(f"Evidence: {f_finding}")
            
    if imp_text.strip():
        i_finding = extract_gb_paragraphs(imp_text)
        if i_finding:
            if not f_finding or i_finding not in f_finding:
                parts.append(f"Impression: {i_finding}")
                    
    if not parts:
        return "No relevant gallstone context found."
        
    return " | ".join(parts)

@app.post("/api/extract-gallstone")
def extract_data(patient: PatientData):
    # 1. ทำความสะอาดข้อความและตัดมาเฉพาะเรื่องนิ่ว
    cleaned_text = clean_medical_text(patient.raw_text)
    
    if cleaned_text == "No relevant gallstone context found.":
        return {
            "gallstone_found": False,
            "size_min": None,
            "size_max": None,
            "size_summation": None,
            "unit": None,
            "_note": "ไม่มีคีย์เวิร์ดเกี่ยวกับถุงน้ำดีใน Report"
        }
    
    # 2. ยิงไปหา Ollama ที่อยู่บน Windows
    # ใช้ Prompt สั้นๆ เพราะกฎยาวๆ ถูกฝังใน Modelfile ของ Ollama แล้ว
    user_prompt = f"Extract gallstone information from this report:\n\n{cleaned_text}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0 # ปิดการสุ่มเดา
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        ai_response_text = response.json().get("response", "").strip()
        
        # 3. แปลงคำตอบที่เป็น String กลับเป็น JSON Object คืนให้ SS
        try:
            start_idx = ai_response_text.find('{')
            end_idx = ai_response_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                clean_pred = ai_response_text[start_idx:end_idx+1]
                final_json = json.loads(clean_pred)
            else:
                final_json = json.loads(ai_response_text)
                
            return final_json
            
        except json.JSONDecodeError:
            return {"error": "AI response is not valid JSON", "raw_response": ai_response_text}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")

# Health Check Route สำหรับให้ Docker เช็คว่าระบบปกติดีไหม และเช็ค Ollama ด้วย
@app.get("/health")
def health_check():
    status_data = {"backend": "running"}
    base_ollama_url = OLLAMA_URL.replace("/api/generate", "")
    
    try:
        response = requests.get(base_ollama_url, timeout=3)
        if response.status_code == 200:
            status_data["ollama"] = "ready"
            status_data["overall_status"] = "System is fully operational"
        else:
            status_data["ollama"] = f"error (status code: {response.status_code})"
            status_data["overall_status"] = "Not ready: Ollama returned an error"
    except Exception:
        status_data["ollama"] = "down or unreachable"
        status_data["overall_status"] = "Not ready: Cannot connect to Ollama"
        
    return status_data
