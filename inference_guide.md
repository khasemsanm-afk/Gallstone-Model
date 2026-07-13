# 🩺 คู่มือการนำ AI (MedGemma - Gallstone) ไปใช้งานจริง (Inference Guide)

ตอนนี้คุณหมอมีไฟล์สมองของ AI (โฟลเดอร์ `unsloth_medgemma_v2`) อยู่ในเครื่องแล้วครับ ขั้นตอนต่อไปคือการ "ปลุกมันขึ้นมาตอบคำถาม" ครับ

## 📌 สิ่งที่ต้องรู้ก่อนเริ่ม
ตัวไฟล์ที่คุณหมอโหลดมา มันคือ **"ความรู้เสริม (LoRA Adapters)"** ครับ เวลานำไปใช้งานจริง โปรแกรมจะทำการดึง **"ร่างต้น (MedGemma 4B)"** จากอินเทอร์เน็ต มาประกอบร่างรวมกับความรู้เสริมที่คุณหมอเทรนไว้แบบอัตโนมัติครับ

---

## 💻 วิธีนำไปทดสอบใช้งาน (ผ่าน Python)

เพื่อให้คุณหมอสามารถพิมพ์คุยโต้ตอบกับ AI ได้เหมือน ChatGPT ผมได้เตรียมโค้ดสำหรับนำไปใช้งานไว้ให้แล้วครับ

### 1. สร้างไฟล์สคริปต์สำหรับเรียกใช้งาน
ให้คุณหมอเข้าไปที่โฟลเดอร์ `D:\Work\finetune\qlora_gallstone_v2\scripts\`
แล้วสร้างไฟล์ใหม่ชื่อว่า **`03_inference.py`** จากนั้นก๊อปปี้โค้ดด้านล่างนี้ไปวางแล้วกดเซฟครับ:

```python
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch

# 1. ตั้งค่าและโหลดโมเดล
print("กำลังปลุก AI... (อาจใช้เวลาสักครู่)")
model_path = r"D:\Work\finetune\qlora_gallstone_v2\models\unsloth_medgemma_v2" # พาทที่เก็บโมเดลของเรา

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_path,
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True, # โหลดแบบบีบอัดเพื่อให้กินแรมน้อยลง
)

# เปิดโหมดความเร็วสูงสำหรับตอบคำถาม (Inference Mode)
FastLanguageModel.for_inference(model)

# ตั้งค่ารูปแบบการคุยให้เป็น ChatML (แบบเดียวกับตอนที่เราสอนมัน)
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "chatml",
    mapping = {"role": "role", "content": "content", "user": "user", "assistant": "assistant"}, 
)

# 2. ฟังก์ชันสำหรับคุยโต้ตอบ
def chat_with_ai(prompt_text):
    # จัดรูปแบบคำถาม
    messages = [{"role": "user", "content": prompt_text}]
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize = True,
        add_generation_prompt = True,
        return_tensors = "pt"
    ).to("cuda")

    # สั่งให้ AI คิดและพิมพ์คำตอบ
    outputs = model.generate(input_ids = inputs, max_new_tokens = 512, use_cache = True)
    
    # แปลงผลลัพธ์จากตัวเลขเป็นข้อความภาษาคน
    response = tokenizer.batch_decode(outputs, skip_special_tokens = True)[0]
    
    # ตัดส่วนที่เป็นคำถามออก เอาเฉพาะคำตอบ
    answer = response.split("assistant\n")[-1]
    return answer.strip()

# 3. เริ่มต้นใช้งานจริง
print("\n" + "="*50)
print("✅ AI พร้อมใช้งานแล้ว! พิมพ์คำถามของคุณหมอได้เลยครับ (พิมพ์ 'exit' เพื่อออก)")
print("="*50 + "\n")

while True:
    user_input = input("👨‍⚕️ คุณหมอ: ")
    if user_input.lower() == 'exit':
        print("ปิดระบบการทำงาน...")
        break
        
    print("🤖 AI กำลังคิด...")
    answer = chat_with_ai(user_input)
    print(f"\n🤖 AI: {answer}\n")
    print("-" * 50)
```

### 2. วิธีรันเพื่อพูดคุยกับ AI
การจะรันโมเดลนี้ได้ คอมพิวเตอร์ของคุณหมอจำเป็นต้องมี **การ์ดจอแยกของ NVIDIA** และติดตั้ง Python เอาไว้ครับ (เหมือนที่เราทำใน Server)
*   **ถ้าคอมพิวเตอร์ของคุณหมอแรงพอ (มีการ์ดจอ NVIDIA แรม 6GB ขึ้นไป):** สามารถเปิด Command Prompt / PowerShell รันสคริปต์นี้ในเครื่องตัวเองได้เลยครับ
*   **ถ้ารันบนเครื่องตัวเองไม่ไหว:** คุณหมอสามารถเอาโฟลเดอร์ `unsloth_medgemma_v2` อัปโหลดขึ้น Google Drive แล้วเอาไปรันบนเว็บ **Google Colab** (เลือก T4 GPU ฟรี) โดยใช้โค้ดตัวเดียวกันนี้ได้เลยครับ!

---

## 🚀 ก้าวต่อไป (ถ้านำไปใช้ในแอปพลิเคชันหรือคลินิก)

หากในอนาคตคุณหมอต้องการเอาไปต่อยอดทำเป็น **Web App หรือ LINE Bot** ให้คนไข้ใช้งานจริง:
1. คุณหมอสามารถดัดแปลงไฟล์ `03_inference.py` ข้างต้น ให้กลายเป็น **API (เช่นใช้ FastAPI)**
2. เอา API นี้ไปรันไว้บน Server ที่มีการ์ดจอ (เช่น Google Cloud ที่เราเช่าเมื่อคืน)
3. เขียนโปรแกรมเชื่อมต่อจาก LINE หรือเว็บไซต์ ให้ส่งข้อความคนไข้เข้ามาที่ API ตัวนี้ และส่งคำตอบของ AI กลับไปหาคนไข้ครับ

*ปล. ถ้าต้องการแปลงร่างโมเดลให้กลายเป็นไฟล์เดี่ยวๆ ตัวเล็กๆ เอาไปรันบนคอมธรรมดาโดยไม่ต้องใช้การ์ดจอ (เรียกว่าไฟล์ GGUF) สามารถแจ้งผมได้เลยครับ! (Unsloth มีระบบแปลงร่างที่ง่ายมากๆ ครับ)*
