from typing import Any


import json
from tqdm import tqdm
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import warnings
warnings.filterwarnings('ignore') # ซ่อนข้อความแจ้งเตือนยิบย่อย

# 1. โหลดโมเดล
print("กำลังปลุก AI เพื่อเตรียมทำข้อสอบ... (รอสักครู่)")
model_path = "unsloth_medgemma_v2"
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_path, max_seq_length=2048, dtype=None, load_in_4bit=True
)
FastLanguageModel.for_inference(model)
tokenizer = get_chat_template(tokenizer, chat_template="chatml", mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"})

# 2. โหลดไฟล์ข้อสอบ (val.jsonl)
val_data = []
print("กำลังโหลดข้อสอบ (ชุด Validation)...")
with open("val.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        val_data.append(json.loads(line))

# 3. ตัวแปรเก็บคะแนน
total_cases = len(val_data)
correct_found = 0
true_positive = 0
false_positive = 0
true_negative = 0
false_negative = 0
size_evals = 0
size_correct = 0

print(f"\nเริ่มทำข้อสอบทั้งหมด {total_cases} ข้อ... (อาจใช้เวลาประมาณ 5-10 นาที ไปชงกาแฟรอได้เลยครับ)")

# 4. ลุยทำข้อสอบทีละข้อ
for case in tqdm[Any](val_data, desc="AI กำลังทำข้อสอบ"):
    messages = case["messages"]
    user_msg = next(m["content"] for m in messages if m["role"] == "user")
    truth_msg = next(m["content"] for m in messages if m["role"] == "assistant")
    
    # ให้ AI เดาคำตอบ (ใส่ attention_mask และปิดการเดาสุ่มเพื่อให้แม่นยำและทำงานไวสุดๆ)
    text_prompt = tokenizer.apply_chat_template([{"role": "user", "content": user_msg}], tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text_prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask, # แก้บั๊กความช้าตรงนี้ครับ!
            max_new_tokens=256,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False # บังคับตอบตรงๆ ไม่แต่งเรื่อง
        )
    response = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    
    # ตัดเอาเฉพาะคำตอบของ AI
    try:
        pred_str = response.split("assistant\n")[-1].strip()
        truth = json.loads(truth_msg)
        pred = json.loads(pred_str)
        
        # กฎข้อที่ 1: ตรวจว่าหานิ่วเจอถูกต้องไหม (True/False)
        truth_found = truth.get("gallstone_found")
        pred_found = pred.get("gallstone_found")
        
        if pred_found == truth_found:
            correct_found += 1
            if truth_found is True:
                true_positive += 1
            else:
                true_negative += 1
        else:
            if truth_found is True:
                false_negative += 1
            else:
                false_positive += 1
                
        # กฎข้อที่ 2: ถ้าเป็นเคสที่มีนิ่วทั้งคู่ ให้ตรวจว่าสกัด "ขนาดนิ่ว" ตรงเป๊ะไหม
        if truth_found is True and pred_found is True:
            size_evals += 1
            # ดึงค่าขนาดมาเทียบกัน
            t_w, t_l, t_d = truth.get("size_width_cm"), truth.get("size_length_cm"), truth.get("size_depth_cm")
            p_w, p_l, p_d = pred.get("size_width_cm"), pred.get("size_length_cm"), pred.get("size_depth_cm")
            
            # ถ้าขนาดเท่ากันเป๊ะ (ให้คะแนนเต็ม)
            if str(t_w) == str(p_w) and str(t_l) == str(p_l) and str(t_d) == str(p_d):
                size_correct += 1

    except Exception as e:
        # ถ้า AI พิมพ์มั่วจนไม่ใช่รูปแบบ JSON ให้ถือว่าตอบผิด
        truth = json.loads(truth_msg)
        if truth.get("gallstone_found") is True:
            false_negative += 1
        else:
            false_positive += 1

# 5. สรุปผลสอบ
print("\n" + "="*50)
print("📊 ผลการสอบความแม่นยำของ AI (Evaluation Report)")
print("="*50)
print(f"จำนวนข้อสอบทั้งหมด (Validation Set): {total_cases} เคส")
print(f"✅ ทายถูกว่า 'มี/ไม่มี' นิ่ว (Accuracy): {(correct_found/total_cases)*100:.2f}% ({correct_found}/{total_cases})")
print("-" * 50)
if (true_positive + false_negative) > 0:
    sensitivity = true_positive / (true_positive + false_negative)
    print(f"🩺 ความไว (Sensitivity): {sensitivity*100:.2f}% (จากเคสที่มีนิ่วจริง AI หาเจอเกือบหมดไหม)")
if (true_negative + false_positive) > 0:
    specificity = true_negative / (true_negative + false_positive)
    print(f"🛡️ ความจำเพาะ (Specificity): {specificity*100:.2f}% (จากเคสที่ไม่มีนิ่ว AI หลุดวินิจฉัยผิดไหม)")
print("-" * 50)
if size_evals > 0:
    print(f"📏 สกัดขนาดนิ่ว (กว้างxยาวxลึก) ได้ถูกต้องเป๊ะ: {(size_correct/size_evals)*100:.2f}% ({size_correct}/{size_evals} เคส)")
print("="*50)
print("หมายเหตุ: ค่านำไปอ้างอิงและปรับจูนโมเดลต่อได้เลยครับ!")
