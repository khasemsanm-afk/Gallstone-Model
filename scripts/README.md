# คู่มือการต่อยอดโปรเจกต์: วิธีสร้าง AI สกัดข้อมูลโรคใหม่ (ฉบับละเอียดยิบ)

> **เอกสารนี้เขียนขึ้นสำหรับผู้ที่ไม่เคยทำโปรเจกต์นี้มาก่อน** ให้สามารถอ่านแล้วทำตามได้ตั้งแต่ต้นจนจบ
> โดยไม่ต้องถามใคร เพียงแค่เปลี่ยนจาก "นิ่วในถุงน้ำดี (Gallstone)" เป็นโรคอื่นที่ต้องการ

---

## 📖 สารบัญ

1. [ความเข้าใจพื้นฐานก่อนเริ่ม](#-ความเข้าใจพื้นฐานก่อนเริ่ม)
2. [สิ่งที่ต้องเตรียม (Prerequisites)](#-สิ่งที่ต้องเตรียม-prerequisites)
3. [แผนภาพสรุป Workflow](#️-แผนภาพสรุป-workflow)
4. [สเต็ป 0: สร้างโฟลเดอร์โปรเจกต์ใหม่](#-สเต็ป-0-สร้างโฟลเดอร์โปรเจกต์ใหม่)
5. [สเต็ป 1: เตรียมข้อมูล Excel](#-สเต็ป-1-เตรียมข้อมูล-excel)
6. [สเต็ป 2: แปลงข้อมูลเป็น JSONL](#-สเต็ป-2-แปลงข้อมูลเป็น-jsonl-สคริปต์-01_generate_jsonlpy)
7. [สเต็ป 3: เทรนโมเดลบน Cloud](#-สเต็ป-3-เทรนโมเดลบน-cloud-สคริปต์-02_train_unslothpy)
8. [สเต็ป 4: แปลงโมเดลเป็น GGUF](#-สเต็ป-4-แปลงโมเดลเป็น-gguf-สคริปต์-05_export_to_ollamapy)
9. [สเต็ป 5: สร้าง Modelfile](#-สเต็ป-5-สร้าง-modelfile)
10. [สเต็ป 6: ลงโมเดลบน Ollama](#-สเต็ป-6-ลงโมเดลบน-ollama)
11. [สเต็ป 7: ทดสอบโมเดล](#-สเต็ป-7-ทดสอบโมเดล-สคริปต์-06_evaluate_ollamapy)
12. [สเต็ป 8: ปรับ Backend API](#-สเต็ป-8-ปรับ-backend-api-ไฟล์-backendmainpy)
13. [Checklist สรุปรายการตรวจสอบ](#-checklist-สรุปรายการตรวจสอบ)
14. [FAQ ปัญหาที่พบบ่อย](#-faq-ปัญหาที่พบบ่อย)

---



## 📚 ความเข้าใจพื้นฐานก่อนเริ่ม



### โปรเจกต์นี้ทำอะไร?

โปรเจกต์นี้คือ **ระบบ AI ที่อ่านผลอัลตราซาวด์ (ข้อความภาษาอังกฤษ) แล้วสกัดข้อมูลออกมาเป็น JSON อัตโนมัติ**
ตัวอย่าง: ส่งข้อความ "Gallbladder shows a 1.5 cm echogenic gallstone" เข้าไป → AI ตอบกลับ `{"gallstone_found": true, "size_min": 1.5, ...}`

### เทคโนโลยีที่ใช้ (ไม่ต้องเข้าใจลึก แค่รู้ชื่อ)


| เทคโนโลยี           | ทำหน้าที่อะไร                                                                     |
| ------------------- | --------------------------------------------------------------------------------- |
| **QLoRA + Unsloth** | เทคนิคสอน AI ที่ประหยัดทรัพยากรมาก (ใช้ GPU ระดับกลางได้)                         |
| **MedGemma**        | โมเดล AI ตั้งต้นจาก Google ที่ถูกออกแบบมาสำหรับงานทางการแพทย์                     |
| **GGUF**            | รูปแบบไฟล์ AI ที่ถูกบีบอัดให้เล็กลง เพื่อรันบนเครื่องทั่วไปได้                    |
| **Ollama**          | โปรแกรมที่ใช้รัน AI บนเครื่อง Local (ไม่ต้องต่อเน็ต)                              |
| **FastAPI**         | เว็บเซิร์ฟเวอร์ที่รับคำขอ (HTTP Request) จากระบบโรงพยาบาล (SS)                    |
| **Docker**          | กล่องสำเร็จรูปที่บรรจุ Backend ไว้ สั่งรันได้ทุกเครื่องโดยไม่ต้องติดตั้งอะไรเพิ่ม |




### ระบบทำงานอย่างไร? (สรุปสั้นๆ)

```
ระบบ SS โรงพยาบาล → ส่งข้อความอัลตราซาวด์ → FastAPI Backend (คัดกรอง) → Ollama AI (วิเคราะห์) →  FastAPI Backend (คัดกรอง) → ส่ง JSON กลับ SS
```

---



## 🧰 สิ่งที่ต้องเตรียม (Prerequisites)



### สำหรับขั้นตอนเตรียมข้อมูล (ทำบนเครื่องคอมพิวเตอร์ส่วนตัว)

- **Python 3.10+** ติดตั้งบนเครื่อง
- **ไลบรารี Python:** `pandas`, `openpyxl` (สำหรับอ่าน Excel)
  ```bash
  pip install pandas openpyxl
  ```



### สำหรับขั้นตอนเทรนโมเดล (ทำบน Cloud)

- **บัญชี Google Cloud Platform (GCP)** หรือ Google Colab Pro
- **GPU:** อย่างน้อย NVIDIA L4 (VRAM 24 GB) หรือ T4 (VRAM 16 GB)
- **Hugging Face Account:** ต้อง Login เพื่อดาวน์โหลดโมเดล MedGemma
  ```bash
  pip install huggingface_hub
  huggingface-cli login
  # ระบบจะถาม Token → ไปก็อปปี้ที่ https://huggingface.co/settings/tokens
  ```
- **ไลบรารีบน Cloud:**
  ```bash
  pip install unsloth torch trl transformers datasets
  ```



### สำหรับขั้นตอน Deploy (ทำบน Server โรงพยาบาล)

- **เครื่อง Linux Server** ที่ติดตั้ง Docker แล้ว
- **Ollama** ติดตั้งบน Server แล้ว (ดาวน์โหลดที่ [https://ollama.com](https://ollama.com))

---



## 📁 สเต็ป 0: สร้างโฟลเดอร์โปรเจกต์ใหม่

**ทำไมต้องสร้างโฟลเดอร์ใหม่?** เพื่อไม่ให้โค้ดไปปนกับโปรเจกต์ Gallstone เดิม

1. ก็อปปี้โฟลเดอร์ `qlora_gallstone` ทั้งก้อนแล้วตั้งชื่อใหม่:
  ```bash
   # ตัวอย่าง: ถ้าจะทำเรื่อง "นิ่วในไต"
   cp -r qlora_gallstone qlora_kidney_stone
   cd qlora_kidney_stone
  ```
2. ลบไฟล์ข้อมูลเก่าที่ไม่เกี่ยวข้อง:
  ```bash
   rm -rf data/processed/*.jsonl
   rm -rf data/processed/*.xlsx
   rm -rf models/*
   rm -rf Model_500/*
  ```
3. โครงสร้างโฟลเดอร์ที่ควรได้:
  ```
   qlora_kidney_stone/
   ├── scripts/
   │   ├── 01_generate_jsonl.py    ← แก้ไข
   │   ├── 02_train_unsloth.py     ← แก้ไขเล็กน้อย
   │   ├── 05_export_to_ollama.py  ← แก้ไขเล็กน้อย
   │   └── 06_evaluate_ollama.py   ← แก้ไข
   ├── backend/
   │   ├── main.py                 ← แก้ไข
   │   ├── Dockerfile              ← ไม่ต้องแก้
   │   ├── docker-compose.yml      ← แก้ชื่อ container (ถ้าต้องการ)
   │   └── requirements.txt        ← ไม่ต้องแก้
   ├── data/
   │   ├── raw/                    ← ใส่ไฟล์ Excel ดิบที่นี่
   │   └── processed/              ← ไฟล์ JSONL จะถูกสร้างที่นี่
   ├── Modelfile                   ← แก้ไข
   └── README.md                   ← อัปเดตให้ตรงกับโปรเจกต์ใหม่
  ```

---



## 📊 สเต็ป 1: เตรียมข้อมูล Excel



### ไฟล์ Excel ต้องมีคอลัมน์อะไรบ้าง?

**คอลัมน์ที่ 1 (Input - ข้อมูลเข้า):**
ต้องมีคอลัมน์ที่เก็บ **ข้อความผลอัลตราซาวด์** (หรือข้อความทางการแพทย์) ตัวอย่างชื่อคอลัมน์: `report_text`

**คอลัมน์ที่ 2 เป็นต้นไป (Output - คำตอบ):**
ต้องมีคอลัมน์ที่เก็บ **ค่าที่คุณต้องการให้ AI สกัดออกมา** ซึ่งแล้วแต่โรคที่ทำ

#### ตัวอย่างเปรียบเทียบ:

**โปรเจกต์เดิม (Gallstone):**


| report_text                         | gallstone_found | gallstone_size_min | gallstone_size_max | gallstone_size_summation | gallstone_size_unit |
| ----------------------------------- | --------------- | ------------------ | ------------------ | ------------------------ | ------------------- |
| Gallbladder shows a 1.5 cm stone... | TRUE            | 1.5                | 1.5                |                          | cm                  |
| Normal gallbladder...               | FALSE           |                    |                    |                          |                     |


**ตัวอย่างโปรเจกต์ใหม่ (Kidney Stone):**


| report_text                           | kidney_stone_found | location | size_mm |
| ------------------------------------- | ------------------ | -------- | ------- |
| Left kidney shows a 12 mm calculus... | TRUE               | left     | 12      |
| Kidneys are normal...                 | FALSE              |          |         |


**ตัวอย่างโปรเจกต์ใหม่ (Liver Tumor):**


| report_text                               | tumor_found | tumor_type | size_cm | location   |
| ----------------------------------------- | ----------- | ---------- | ------- | ---------- |
| A 3.2 cm hypoechoic mass at right lobe... | TRUE        | mass       | 3.2     | right lobe |
| Normal liver parenchyma...                | FALSE       |            |         |            |




### จำนวนข้อมูลที่แนะนำ

- **แนะนำ:** 500-1,000 เคส (ผลลัพธ์ดีแต่ AI อาจยังไม่ค่อยแม่นยำ)
- **ดีมาก:** 1,500+ เคส (โปรเจกต์ Gallstone ของเราใช้ ~1,700 เคส)
- **ควรมีสัดส่วนที่สมดุล** ระหว่างเคสที่ "พบ" กับ "ไม่พบ" (เช่น 60:40 หรือ 70:30)



### เสร็จแล้วเซฟไฟล์ Excel ไว้ที่:

```
qlora_kidney_stone/data/raw/training_data.xlsx
```

---



## 🔄 สเต็ป 2: แปลงข้อมูลเป็น JSONL (สคริปต์ `01_generate_jsonl.py`)



### ไฟล์นี้ทำอะไร?

อ่าน Excel → สร้าง "ชุดข้อสอบพร้อมเฉลย" ในรูปแบบที่ AI เข้าใจ (JSONL) → แบ่งเป็น 2 ชุด:

- `train.jsonl` (85%) = ชุดที่ใช้สอน AI
- `val.jsonl` (15%) = ชุดที่ใช้ทดสอบความแม่นยำหลังเรียนจบ

% สามารถปรับเปลี่ยนได้ตามความเหมาะสม

### จุดที่ต้องแก้ไข (มีทั้งหมด 4 จุด):



#### จุดที่ 1: เปลี่ยน Path ไฟล์ (บรรทัดที่ 7-9)

```python
# จากเดิม:
INPUT_EXCEL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\pruned_training_data_relaxed_fixed.xlsx"
TRAIN_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\train.jsonl"
VAL_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\val.jsonl"

# เปลี่ยนเป็น:
INPUT_EXCEL = r"D:\Work\finetune\qlora_kidney_stone\data\raw\training_data.xlsx"
TRAIN_JSONL = r"D:\Work\finetune\qlora_kidney_stone\data\processed\train.jsonl"
VAL_JSONL = r"D:\Work\finetune\qlora_kidney_stone\data\processed\val.jsonl"
```



#### จุดที่ 2: เปลี่ยน System Prompt (บรรทัดที่ 11-21)

System Prompt คือ "กฎเหล็ก" ที่บอก AI ว่ามันต้องสกัดอะไร ต้องตอบในรูปแบบไหน

```python
# จากเดิม (Gallstone):
SYSTEM_PROMPT = """You are an expert medical AI assistant specialized in analyzing ultrasound reports. 
Your task is to extract information about gallstones and format it strictly as a JSON object.

Extraction Rules:
1. 'gallstone_found': boolean. Set to true if gallstones are present...
...
Output ONLY the JSON object. Do not include markdown formatting or explanations."""

# เปลี่ยนเป็น (ตัวอย่าง Kidney Stone):
SYSTEM_PROMPT = """You are an expert medical AI assistant specialized in analyzing ultrasound reports. 
Your task is to extract information about kidney stones and format it strictly as a JSON object.

Extraction Rules:
1. 'kidney_stone_found': boolean. Set to true if kidney stones are present. Set to false if absent.
2. 'location': string. Where the stone is located ('left', 'right', or 'both'). Set to null if not found.
3. 'size_mm': float. The size of the stone in millimeters. Set to null if not specified.

Output ONLY the JSON object. Do not include markdown formatting or explanations."""
```

> **💡 เคล็ดลับสำคัญ:** System Prompt ใน 01_generate_jsonl.py **ต้องตรงกันเป๊ะ** กับ System Prompt ใน Modelfile (สเต็ป 5) เพราะ AI ถูกสอนด้วยกฎชุดไหน มันจะจำกฎชุดนั้น ถ้าตอน Deploy ใช้กฎชุดอื่น AI จะสับสน



#### จุดที่ 3: เปลี่ยนโครงสร้าง JSON เป้าหมาย (บรรทัดที่ 23-34)

ส่วนนี้คือ ฟังก์ชันที่อ่าน Excel แล้วสร้าง JSON คำตอบ ต้องแก้ให้ตรงกับคอลัมน์ใน Excel ของคุณ

```python
# จากเดิม (Gallstone):
def create_message(row):
    user_text = str(row['relaxed_pruned_report'])
    target_json = {
        "gallstone_found": bool(row['gallstone_found']) if pd.notna(row['gallstone_found']) else False,
        "size_min": float(row['gallstone_size_min']) if pd.notna(row['gallstone_size_min']) else None,
        "size_max": float(row['gallstone_size_max']) if pd.notna(row['gallstone_size_max']) else None,
        "size_summation": float(row['gallstone_size_summation']) if pd.notna(row['gallstone_size_summation']) else None,
        "unit": str(row['gallstone_size_unit']) if pd.notna(row['gallstone_size_unit']) else None
    }

# เปลี่ยนเป็น (ตัวอย่าง Kidney Stone):
def create_message(row):
    user_text = str(row['report_text'])  # ← ชื่อคอลัมน์ข้อความใน Excel ของคุณ
    target_json = {
        "kidney_stone_found": bool(row['kidney_stone_found']) if pd.notna(row['kidney_stone_found']) else False,
        "location": str(row['location']) if pd.notna(row['location']) else None,
        "size_mm": float(row['size_mm']) if pd.notna(row['size_mm']) else None,
    }
```

> **⚠️ สำคัญมาก:** ชื่อใน `row['...']` ต้องตรงกับชื่อหัวคอลัมน์ใน Excel (ตัวพิมพ์เล็กใหญ่ด้วย)



#### จุดที่ 4: เปลี่ยนข้อความ Prompt ขาเข้า (บรรทัดที่ 40)

```python
# จากเดิม:
{"role": "user", "content": f"Extract gallstone information from this report:\n\n{user_text}"}

# เปลี่ยนเป็น: (ตัวอย่าง)
{"role": "user", "content": f"Extract kidney stone information from this report:\n\n{user_text}"}
```



### วิธีรัน:

```bash
cd scripts
python 01_generate_jsonl.py
```

**ผลลัพธ์ที่ควรได้:** จะปรินต์จำนวนข้อมูล Train/Val และสร้างไฟล์ `train.jsonl` + `val.jsonl` ในโฟลเดอร์ `data/processed/`

---



## 🧠 สเต็ป 3: เทรนโมเดลบน Cloud (สคริปต์ `02_train_unsloth.py`)



### ไฟล์นี้ทำอะไร?

โหลดโมเดล AI ตั้งต้น (MedGemma) → สอนมันด้วยข้อมูลของเรา (QLoRA) → บันทึกโมเดลที่สอนเสร็จแล้ว

### ต้องรันที่ไหน?

**ต้องรันบน Cloud Server ที่มี GPU** (เช่น GCP VM หรือ Google Colab)
ไม่สามารถรันบนคอมพิวเตอร์ทั่วไปได้ เพราะต้องใช้ GPU VRAM อย่างน้อย 16 GB

### วิธีอัปโหลดไฟล์ขึ้น Cloud:

```bash
# อัปโหลดไฟล์ train.jsonl และ val.jsonl ขึ้น Cloud Server
scp data/processed/train.jsonl username@cloud-server:~/training/
scp data/processed/val.jsonl username@cloud-server:~/training/
scp scripts/02_train_unsloth.py username@cloud-server:~/training/
```



### จุดที่ต้องแก้ไข (มี 2 จุด):



#### จุดที่ 1: เปลี่ยนชื่อโฟลเดอร์บันทึกโมเดล (บรรทัดที่ 11)

```python
# จากเดิม:
OUTPUT_DIR = "unsloth_medgemma_v2"

# เปลี่ยนเป็น:
OUTPUT_DIR = "unsloth_kidney_stone_model"
```



#### จุดที่ 2: (ถ้าต้องการ) ปรับจำนวนรอบการเทรน (บรรทัดที่ 84)

```python
# ค่าเริ่มต้นคือ 5 รอบ (Epoch) ซึ่งเหมาะกับข้อมูล 1,500+ เคส ปรับแก้ไขได้ตามความเหมาะสมของข้อมูล
num_train_epochs = 5,
```

> **💡 หมายเหตุ:** ส่วนอื่นๆ ในไฟล์ (เช่น LoRA config, learning rate, batch size) ถูกปรับจูนมาเหมาะสมแล้ว แต่ก็สามารถปรับเปลี่ยนให้เหมาะสมกับข้อมูลที่จะสอน model ได้



### วิธีรัน (บน Cloud):

```bash
cd ~/training
python 02_train_unsloth.py
```

**ใช้เวลาประมาณ:** 30-60 นาที (ขึ้นอยู่กับ GPU และจำนวนข้อมูล)
**ผลลัพธ์:** โฟลเดอร์ `unsloth_kidney_stone_model/` ที่มีไฟล์น้ำหนักของ AI

---



## 📦 สเต็ป 4: แปลงโมเดลเป็น GGUF (สคริปต์ `05_export_to_ollama.py`)



### ไฟล์นี้ทำอะไร?

เอาโมเดลที่เทรนเสร็จ → ผสมรวม (Merge) กับโมเดลตั้งต้น → บีบอัดเป็นไฟล์ GGUF ที่ Ollama รันได้

### ต้องรันที่ไหน?

**ยังคงรันบน Cloud Server เดิม** (เครื่องเดียวกับที่เทรน)

### จุดที่ต้องแก้ไข (มี 2 จุด):



#### จุดที่ 1: เปลี่ยนชื่อโฟลเดอร์โมเดลต้นทาง (บรรทัดที่ 7)

```python
# จากเดิม:
model_path = "unsloth_medgemma_v2"

# เปลี่ยนเป็น (ต้องตรงกับชื่อที่ตั้งในสเต็ป 3):
model_path = "unsloth_kidney_stone_model"
```



#### จุดที่ 2: เปลี่ยนชื่อไฟล์ GGUF (บรรทัดที่ 18)

```python
# จากเดิม:
output_gguf_name = "medgemma-gallstone-q4_k_m.gguf"

# เปลี่ยนเป็น:
output_gguf_name = "medgemma-kidney-q4_k_m.gguf"
```



### วิธีรัน :

```bash
python 05_export_to_ollama.py
```

**ใช้เวลาประมาณ:** 10-15 นาที
**ผลลัพธ์:** โฟลเดอร์ `model_ollama/` ที่มีไฟล์ `.gguf` อยู่ข้างใน

### วิธีดาวน์โหลดไฟล์ GGUF จาก Cloud กลับมาที่เครื่อง:

```bash
# รันบนเครื่องคอมพิวเตอร์ของคุณ (ไม่ใช่บน Cloud)
scp username@cloud-server:~/training/model_ollama/*.gguf ./
```

---



## 📜 สเต็ป 5: สร้าง Modelfile



### Modelfile คืออะไร?

เป็นไฟล์ "คู่มือคำสั่ง" ที่บอก Ollama ว่า:

- ใช้ไฟล์สมอง GGUF ตัวไหน
- ให้ AI พูดคุยในรูปแบบไหน (Template)
- กฎเหล็กของ AI คืออะไร (System Prompt)



### วิธีสร้าง:

สร้างไฟล์ชื่อ `Modelfile` (ไม่มีนามสกุล) ในโฟลเดอร์โปรเจกต์

```text
FROM ./ชื่อไฟล์ggufของคุณ.gguf

TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

SYSTEM """You are an expert medical AI assistant specialized in analyzing ultrasound reports. 
Your task is to extract information about kidney stones and format it strictly as a JSON object.

Extraction Rules:
1. 'kidney_stone_found': boolean. Set to true if kidney stones are present. Set to false if absent.
2. 'location': string. Where the stone is located ('left', 'right', or 'both'). Set to null if not found.
3. 'size_mm': float. The size of the stone in millimeters. Set to null if not specified.

Output ONLY the JSON object. Do not include markdown formatting or explanations."""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
```

> **⚠️ สำคัญมาก:**
>
> - บรรทัด `FROM ./ชื่อไฟล์ggufของคุณ.gguf` ต้องชี้ไปที่ไฟล์ GGUF ที่ถูกต้อง
> - ข้อความใน `SYSTEM """..."""` ต้องเหมือนกับ `SYSTEM_PROMPT` ในสคริปต์ `01_generate_jsonl.py` เป๊ะทุกตัวอักษร (เพราะ AI ถูกสอนด้วยกฎชุดนี้)

---



## ⚙️ สเต็ป 6: ลงโมเดลบน Ollama



### ต้องทำที่ไหน?

บน **Server ที่จะรัน AI จริง** (เครื่อง Linux ของโรงพยาบาล หรือเครื่องคอมพิวเตอร์ที่ติดตั้ง Ollama ไว้แล้ว)

### วิธีทำ:

1. วางไฟล์ `.gguf` และไฟล์ `Modelfile` ไว้ในโฟลเดอร์เดียวกัน
2. เปิด Terminal แล้วเข้าไปที่โฟลเดอร์นั้น
3. รันคำสั่งนี้:
  ```bash
   ollama create medgemma-kidney -f Modelfile
  ```
  - `medgemma-kidney` = ชื่อที่คุณตั้งให้โมเดล (ตั้งอะไรก็ได้ แต่ต้องจำไว้เพราะจะใช้ใน Backend)
4. ตรวจสอบว่าโมเดลถูกสร้างสำเร็จ:
  ```bash
   ollama list
  ```
   ต้องเห็นชื่อ `medgemma-kidney` อยู่ในรายการ
5. ทดสอบรันเบื้องต้น:
  ```bash
   ollama run medgemma-kidney "Left kidney shows a 12 mm calculus at lower pole"
  ```
   ต้องได้ JSON กลับมา เช่น `{"kidney_stone_found": true, "location": "left", "size_mm": 12}`

---



## 🧪 สเต็ป 7: ทดสอบโมเดล (สคริปต์ `06_evaluate_ollama.py`)



### ไฟล์นี้ทำอะไร?

ยิงข้อสอบ (Validation Set) ทั้งหมดไปให้ AI ทำ → เปรียบเทียบคำตอบ AI กับคำตอบจริง → คำนวณเปอร์เซ็นต์ความแม่นยำ → บันทึกข้อที่ AI ตอบผิดเป็น Excel สำหรับแพทย์รีวิว

### จุดที่ต้องแก้ไข (มี 4 จุด):



#### จุดที่ 1: เปลี่ยน Path ไฟล์ข้อสอบ (บรรทัดที่ 8)

```python
# จากเดิม:
VAL_JSONL = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\val.jsonl"

# เปลี่ยนเป็น:
VAL_JSONL = r"D:\Work\finetune\qlora_kidney_stone\data\processed\val.jsonl"
```



#### จุดที่ 2: เปลี่ยนชื่อโมเดล Ollama (บรรทัดที่ 10)

```python
# จากเดิม:
MODEL_NAME = "medgemma-gallstone"

# เปลี่ยนเป็น:
MODEL_NAME = "medgemma-kidney"
```



#### จุดที่ 3: เปลี่ยนชื่อ Key ที่ใช้เทียบคำตอบ (บรรทัดที่ 53, 65, 68, 69)

```python
# จากเดิม (ทุกบรรทัดที่มีคำว่า "gallstone_found"):
truth_json = {"gallstone_found": False}
pred_json = {"gallstone_found": False, "_error": "Invalid JSON"}
truth_found = truth_json.get("gallstone_found", False)
pred_found = pred_json.get("gallstone_found", False)

# เปลี่ยนเป็น:
truth_json = {"kidney_stone_found": False}
pred_json = {"kidney_stone_found": False, "_error": "Invalid JSON"}
truth_found = truth_json.get("kidney_stone_found", False)
pred_found = pred_json.get("kidney_stone_found", False)
```



#### จุดที่ 4: เปลี่ยน Path ไฟล์บันทึกข้อผิดพลาด (บรรทัดที่ 109)

```python
# จากเดิม:
error_file = r"D:\Work\finetune\qlora_gallstone_v2\data\processed\evaluation_errors.xlsx"

# เปลี่ยนเป็น:
error_file = r"D:\Work\finetune\qlora_kidney_stone\data\processed\evaluation_errors.xlsx"
```



### วิธีรัน:

```bash
python 06_evaluate_ollama.py
```

**ผลลัพธ์:** รายงานความแม่นยำ (Accuracy, Sensitivity, Specificity) และไฟล์ Excel ที่เก็บเคสที่ AI ตอบผิด

---



## 🌐 สเต็ป 8: ปรับ Backend API (ไฟล์ `backend/main.py`)



### ไฟล์นี้ทำอะไร?

เป็น "ประตูหน้า" ที่รับคำขอจาก SS System → คัดกรองด้วย Keywords → ส่งไปให้ AI → ส่ง JSON กลับ SS

### จุดที่ต้องแก้ไข (มี 5 จุด):



#### จุดที่ 1: เปลี่ยนชื่อ API Title (บรรทัดที่ 7)

```python
# จากเดิม:
app = FastAPI(title="Gallstone AI Extraction API", version="1.0")

# เปลี่ยนเป็น:
app = FastAPI(title="Kidney Stone AI Extraction API", version="1.0")
```



#### จุดที่ 2: เปลี่ยนชื่อโมเดล Ollama (บรรทัดที่ 11)

```python
# จากเดิม:
MODEL_NAME = "medgemma-gallstone"

# เปลี่ยนเป็น (ต้องตรงกับชื่อที่สร้างในสเต็ป 6):
MODEL_NAME = "medgemma-kidney"
```



#### จุดที่ 3: เปลี่ยนคีย์เวิร์ดคัดกรองด่านหน้า (บรรทัดที่ 17)

คีย์เวิร์ดนี้คือ "ตัวคัดกรอง" ถ้าข้อความที่ส่งเข้ามาไม่มีคำเหล่านี้เลย Backend จะตอบ "ไม่พบ" กลับไปทันทีโดยไม่รบกวน AI

```python
# จากเดิม (Gallstone keywords):
GB_KEYWORDS = re.compile(r"\b(gallbladder|gall\s*bladder|gb|gall\s*stones?|gallstones?|...)\b", re.IGNORECASE)

# เปลี่ยนเป็น (ตัวอย่าง Kidney Stone keywords):
KEYWORDS = re.compile(r"\b(kidney|kidneys|renal|calculus|calculi|nephrolithiasis|urolithiasis|hydronephrosis|stone|stones|pelvis|calyx|calyces|ureter)\b", re.IGNORECASE)
```

> **💡 วิธีหาคีย์เวิร์ด:** เปิดไฟล์ Excel ข้อมูลของคุณ แล้วดูว่าเคสที่ "พบโรค" มักจะมีคำอะไรปรากฏอยู่บ่อยๆ แล้วรวมคำเหล่านั้นมาใส่



#### จุดที่ 3.5: เพิ่มตัวกรอง "คำต้องห้าม" เพื่อป้องกัน AI สับสน (NEGATIVE_KEYWORDS)

> **⚠️ ต้องทำทุกครั้งที่โรคใหม่มีคำว่า `stone` ซ้ำซ้อนกับอวัยวะอื่น** เช่น โปรเจกต์นิ่วในไต (kidney stone) ที่ใช้คำว่า `stone` เหมือนกับนิ่วในถุงน้ำดี

**ปัญหาที่เกิดขึ้น:** ถ้า Backend ดึงคำว่า `stone` จากทุกบรรทัดมารวมกัน AI จะสับสนเมื่อเห็นตัวเลขจากหลายอวัยวะพร้อมกัน เช่น รายงานที่มีทั้งนิ่วถุงน้ำดีและนิ่วในไต Backend จะดึงทั้ง `2.0-2.2 cm gallstone` และ `0.3 cm renal stone` มาให้ AI อ่านในครั้งเดียว ทำให้ AI ตอบ `null` แทนที่จะระบุขนาดที่ถูกต้อง

**วิธีแก้:** เพิ่ม 2 ตัวแปรใหม่ต่อจาก `GB_KEYWORDS`:

```python
# ตัวแปรที่ 1: รายชื่ออวัยวะที่ไม่เกี่ยวข้องกับโรคที่กำลังสกัด
# ถ้าบรรทัดไหนมีคำเหล่านี้ร่วมกับคำว่า stone ให้เตะบรรทัดนั้นทิ้ง
NEGATIVE_KEYWORDS = re.compile(r"\b(kidney|kidneys|renal|urinary|bladder|prostate)\b", re.IGNORECASE)

# ตัวแปรที่ 2: คำที่เจาะจงว่าเป็นโรคของเราแน่ๆ (ยันต์กันผี)
# ถ้าบรรทัดมีคำต้องห้าม แต่ดันมีคำในกลุ่มนี้ด้วย แสดงว่าหมอเขียนรวบยอดมา ให้เก็บไว้ อย่าลบทิ้ง
EXPLICIT_GB_KEYWORDS = re.compile(r"\b(gallbladder|gall\s*bladder|gb|cholelithiasis|gall\s*stones?|gallstones?)\b", re.IGNORECASE)
```

**แล้วปรับฟังก์ชัน `extract_gb_paragraphs` ให้เช็ค 2 ชั้น:**

```python
def extract_gb_paragraphs(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    kept_lines = []
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if GB_KEYWORDS.search(line_clean):                       # ชั้นที่ 1: เจอคำเกี่ยวกับโรคไหม?
            if NEGATIVE_KEYWORDS.search(line_clean):             # ชั้นที่ 2: เจอคำอวัยวะต้องห้ามไหม?
                if not EXPLICIT_GB_KEYWORDS.search(line_clean):  # ถ้าไม่มียันต์กันผี ลบทิ้ง
                    continue
        line_clean = re.sub(r"\s+", " ", line_clean)
        kept_lines.append(line_clean.lower())
    return " ".join(kept_lines)
```

**ตัวอย่างการทำงาน:**

| บรรทัดในรายงาน | ผลลัพธ์ | เพราะ |
|---|---|---|
| `Gallbladder: Two gallstones, size 2.0-2.2 cm.` | ✅ เก็บไว้ | ไม่มีคำต้องห้าม |
| `Kidneys: A 0.3-cm small stone at left kidney.` | ❌ ลบทิ้ง | มีคำว่า `kidney` และไม่มียันต์กันผี |
| `Urinary bladder: No stone or mass.` | ❌ ลบทิ้ง | มีคำว่า `bladder` |
| `Gallbladder stone 2cm. Kidneys normal.` | ✅ เก็บไว้ | มีคำว่า `kidney` แต่มียันต์กันผี `Gallbladder` คุ้มครองอยู่ |

> **💡 หมายเหตุสำหรับโรคอื่น:** ถ้าทำโปรเจกต์นิ่วในไต ให้สลับคำต้องห้าม/ยันต์กันผีตามนี้
> - `NEGATIVE_KEYWORDS` ใส่คำว่า `gallbladder, biliary, cholelithiasis` (ไม่อยากให้ดึงเรื่องถุงน้ำดีมาปน)
> - `EXPLICIT_KEYWORDS` ใส่คำว่า `kidney, renal, nephrolithiasis` (ยันต์กันผีของโปรเจกต์ไต)



#### จุดที่ 4: เปลี่ยนชื่อ API Endpoint และ JSON ด่านสกัด (บรรทัดที่ 57, 61-74)

```python
# จากเดิม:
    if not parts:
        return "No relevant gallstone context found."
...
@app.post("/api/extract-gallstone")
def extract_data(patient: PatientData):
    ...
    if cleaned_text == "No relevant gallstone context found.":
        return {
            "gallstone_found": False,
            "size_min": None,
            ...
            "_note": "ไม่มีคีย์เวิร์ดเกี่ยวกับถุงน้ำดีใน Report"
        }

# เปลี่ยนเป็น:
    if not parts:
        return "No relevant kidney stone context found."
...
@app.post("/api/extract-kidney-stone")
def extract_data(patient: PatientData):
    ...
    if cleaned_text == "No relevant kidney stone context found.":
        return {
            "kidney_stone_found": False,
            "location": None,
            "size_mm": None,
            "_note": "ไม่มีคีย์เวิร์ดเกี่ยวกับไตใน Report"
        }
```



#### จุดที่ 5: เปลี่ยน Prompt ที่ส่งไปหา AI (บรรทัดที่ 78)

```python
# จากเดิม:
user_prompt = f"Extract gallstone information from this report:\n\n{cleaned_text}"

# เปลี่ยนเป็น:
user_prompt = f"Extract kidney stone information from this report:\n\n{cleaned_text}"
```

> **⚠️ อย่าลืม:** ถ้าเปลี่ยนชื่อ Endpoint จาก `/api/extract-gallstone` เป็น `/api/extract-kidney-stone` ต้องแจ้งทีม SS System ด้วยว่า URL เส้นที่เรียก AI เปลี่ยนแล้วนะ

---

---



## ✅ Checklist สรุปรายการตรวจสอบ

ก่อนปล่อยให้ระบบใช้งานจริง ให้เช็คทุกข้อต่อไปนี้:


| #   | รายการ                                                       | ไฟล์ที่เกี่ยวข้อง              | ตรวจแล้ว |
| --- | ------------------------------------------------------------ | ------------------------------ | -------- |
| 1   | Excel มีคอลัมน์ถูกต้อง มีข้อมูลเพียงพอ (1000 + เคส)          | `data/raw/*.xlsx`              | ☐        |
| 2   | System Prompt ใน `01_generate_jsonl.py` ตรงกับใน `Modelfile` | `scripts/01...`, `Modelfile`   | ☐        |
| 3   | ชื่อคอลัมน์ใน `row['...']` ตรงกับหัวคอลัมน์ Excel            | `scripts/01...`                | ☐        |
| 4   | ไฟล์ `train.jsonl` และ `val.jsonl` ถูกสร้างเรียบร้อย         | `data/processed/`              | ☐        |
| 5   | เทรนโมเดลเสร็จ ไม่มี Error                                   | `scripts/02...`                | ☐        |
| 6   | แปลง GGUF เสร็จ มีไฟล์ `.gguf`                               | `scripts/05...`                | ☐        |
| 7   | `Modelfile` ชี้ไปที่ไฟล์ GGUF ที่ถูกต้อง                     | `Modelfile` บรรทัดที่ 1        | ☐        |
| 8   | `ollama create` สำเร็จ เห็นชื่อโมเดลใน `ollama list`         | Terminal                       | ☐        |
| 9   | `06_evaluate_ollama.py` - Accuracy มากกว่า 90%               | `scripts/06...`                | ☐        |
| 10  | `backend/main.py` - ชื่อ `MODEL_NAME` ตรงกับชื่อใน Ollama    | `backend/main.py` บรรทัดที่ 11 | ☐        |
| 11  | `backend/main.py` - Keywords ตรงกับโรคใหม่                   | `backend/main.py` บรรทัดที่ 17 | ☐        |
| 12  | `curl /health` ตอบ `System is fully operational`             | Terminal                       | ☐        |
| 13  | `curl /api/extract-...` ได้ JSON กลับมาถูกต้อง               | Terminal                       | ☐        |
| 14  | แจ้ง URL ใหม่ให้ทีม SS System แล้ว                           | -                              | ☐        |


---



## ❓ FAQ ปัญหาที่พบบ่อย



### Q: เทรนเสร็จแล้ว Accuracy ต่ำมาก (< 80%) ทำอย่างไร?

**A:** สาเหตุที่พบบ่อย:

1. ข้อมูลน้อยเกินไป → เพิ่มข้อมูลให้มากกว่า 500 เคส
2. ข้อมูลไม่สมดุล (เช่น เคส "พบ" มี 90% เคส "ไม่พบ" มีแค่ 10%) → ปรับสัดส่วนให้ใกล้ 60:40
3. System Prompt คลุมเครือ → เขียนกฎให้ชัดเจนขึ้น พร้อมตัวอย่างในกฎ



### Q: AI ตอบเป็น JSON ไม่ถูกรูปแบบ (Invalid JSON)?

**A:** ตรวจสอบว่า:

1. System Prompt มีคำว่า `Output ONLY the JSON object` หรือไม่
2. `Modelfile` มีบรรทัด `PARAMETER stop "<|im_end|>"` หรือไม่ (ป้องกัน AI พิมพ์เกิน)



### Q: `ollama create` แล้วขึ้น Error หาไฟล์ GGUF ไม่เจอ?

**A:** ตรวจสอบว่า:

1. ไฟล์ `.gguf` อยู่ในโฟลเดอร์เดียวกับ `Modelfile`
2. ชื่อไฟล์ในบรรทัด `FROM ./...` ของ Modelfile ตรงกับชื่อไฟล์จริง (ตัวพิมพ์เล็กใหญ่ด้วย)



### Q: จะเปลี่ยนพอร์ตจาก 8001 เป็นตัวอื่นต้องทำอย่างไร?

**A:** แก้ 1 จุด: ไฟล์ `backend/docker-compose.yml` บรรทัดที่ 8

```yaml
command: uvicorn main:app --host 0.0.0.0 --port 8005  # เปลี่ยนตรงนี้
```

แล้วแจ้ง URL ใหม่ให้ทีม SS System ด้วย
