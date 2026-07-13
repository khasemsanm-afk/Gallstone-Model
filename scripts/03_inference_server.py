from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch

# 1. ตั้งค่าและโหลดโมเดล
print("กำลังปลุก AI... (อาจใช้เวลาสักครู่)")
model_path = "unsloth_medgemma_v2" # พาทบน Server

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
    text_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text_prompt, return_tensors="pt").to("cuda")

    # สั่งให้ AI คิดและพิมพ์คำตอบ
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=512,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False
        )
    
    # แปลงผลลัพธ์จากตัวเลขเป็นข้อความภาษาคน
    response = tokenizer.batch_decode(outputs, skip_special_tokens = True)[0]
    
    # ตัดส่วนที่เป็นคำถามออก เอาเฉพาะคำตอบ
    answer = response.split("assistant\n")[-1]
    return answer.strip()

# 3. เริ่มต้นใช้งานจริง
print("\n" + "="*50)
print("✅ AI พร้อมใช้งานแล้ว! พิมพ์ประวัติคนไข้ที่ต้องการให้ AI วิเคราะห์ได้เลยครับ (พิมพ์ 'exit' เพื่อออก)")
print("="*50 + "\n")

while True:
    user_input = input("👨‍⚕️ คุณหมอ: ")
    if user_input.lower() == 'exit':
        print("ปิดระบบการทำงาน...")
        break
        
    print("🤖 AI กำลังวิเคราะห์...")
    answer = chat_with_ai(user_input)
    print(f"\n🤖 AI: {answer}\n")
    print("-" * 50)
