from unsloth import FastLanguageModel
import os

print("กำลังเตรียมแปลงร่าง Model เป็น GGUF สำหรับ Ollama...")

# 1. โหลดโมเดลที่เราเทรนเสร็จแล้ว
model_path = "unsloth_medgemma_v2"
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_path,
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

# 2. ตั้งค่าการแปลงไฟล์
# "q4_k_m" คือรูปแบบ GGUF ที่สมดุลที่สุด (ไฟล์เล็ก รันเร็ว และแม่นยำสูง)
quantization_method = "q4_k_m" 
output_gguf_name = "medgemma-gallstone-q4_k_m.gguf"

print(f"\nกำลังรวมร่างและแปลงเป็นไฟล์ {output_gguf_name}...")
print("ขั้นตอนนี้อาจใช้เวลาประมาณ 10-15 นาที ห้ามปิดหน้าจอนะครับ!\n")

# 3. สั่ง Export
model.save_pretrained_gguf("model_ollama", tokenizer, quantization_method = quantization_method)

print("\n" + "="*50)
print("✅ แปลงไฟล์เสร็จสมบูรณ์!")
print("ไฟล์สำหรับ Ollama ของคุณถูกเซฟไว้ที่โฟลเดอร์: model_ollama")
print("="*50 + "\n")
