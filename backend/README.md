# MedGemma Gallstone Backend API

ระบบ API สำหรับการสกัดข้อมูลนิ่วในถุงน้ำดีจากข้อความทางการแพทย์ (Ultrasound Reports) โดยใช้โมเดล AI (MedGemma) ที่ถูก Fine-tuned มาเฉพาะทาง ระบบนี้ถูกออกแบบให้ส่วนของ Backend ทำงานอยู่บน **Docker** เพื่อความง่ายในการขยายสเกล และให้ส่วนของ AI ประมวลผลบน **Ollama (Host Machine)** เพื่อรีดประสิทธิภาพการทำงานสูงสุด

---

## สถาปัตยกรรมระบบ (Architecture)
- **API Server:** รันบน Docker Container (FastAPI, Python 3.10) ทำหน้าที่รับคำขอ, คัดกรองข้อมูล, และจัดรูปแบบคำตอบ
- **AI Engine:** รันแบบ Native บน Windows Host Machine ผ่าน Ollama (CPU-based inference)

*(เหตุผลที่แยกกัน เพื่อให้ Docker ไม่แย่งทรัพยากร (RAM) กับ AI และไม่ต้องจัดการเรื่องการส่งผ่าน Hardware (GPU/CPU) เข้าไปใน Container ให้ซับซ้อน)*

---

## วิธีติดตั้งและรันระบบ (Setup & Run)

### 1. ฝั่ง AI (Ollama บนเครื่อง Host)
ระบบนี้ต้องการโมเดล AI `medgemma-gallstone` ให้รันอยู่บน Ollama ในเครื่อง Host
1. ติดตั้ง Ollama จาก `https://ollama.com`
2. สร้าง Modelfile และติดตั้งโมเดล: `ollama create medgemma-gallstone -f Modelfile`
3. ตรวจสอบว่า Ollama รันอยู่ที่ Port 11434 (เป็นค่าเริ่มต้น)

### 2. ฝั่ง Backend API (Docker)
1. ติดตั้ง **Docker Desktop** สำหรับ Windows
2. เปิด PowerShell และเข้าไปที่โฟลเดอร์นี้:
   ```powershell
   cd D:\Work\finetune\qlora_gallstone_v2\backend
   ```
3. รันคำสั่งสร้างและเปิดคอนเทนเนอร์:
   ```powershell
   docker-compose up -d --build
   ```
4. ตรวจสอบการทำงานของ Backend ว่าออนไลน์หรือไม่ โดยเข้าไปที่เบราว์เซอร์:
   > `http://localhost:8000/health` (ควรขึ้นข้อความว่า Backend is running and ready)

---

## คู่มือเชื่อมต่อ API (สำหรับทีมพัฒนาระบบโรงพยาบาล SS)

ระบบสื่อสารด้วย **JSON** ผ่านโพรโทคอล **HTTP POST** แบบ Synchronous (รอรับผลทันที ใช้เวลาประมาณ 2-5 วินาทีต่อ 1 รีเควสต์)

### Endpoint: `/api/extract-gallstone`

- **Method:** `POST`
- **URL:** `http://localhost:8000/api/extract-gallstone`
- **Content-Type:** `application/json`

#### Request Payload
ระบบต้องการรับข้อความดิบ (Raw Text) ของผลอัลตราซาวด์
```json
{
  "raw_text": "Evidence: The gallbladder is distended and contains multiple small gallstones, size up to 1.5 cm..."
}
```

#### Response (กรณีเจอคีย์เวิร์ดและ AI สกัดได้)
```json
{
  "gallstone_found": true,
  "size_min": null,
  "size_max": 1.5,
  "size_summation": null,
  "unit": "cm"
}
```

#### Response (กรณีที่ในข้อความไม่มีการพูดถึงถุงน้ำดีเลย)
ระบบ Backend จะมีฟังก์ชันสแกนคีย์เวิร์ดก่อน หากไม่พบคำที่เกี่ยวกับถุงน้ำดี ระบบจะไม่ส่งต่อให้ AI (เพื่อประหยัดทรัพยากร) และจะตอบกลับทันที:
```json
{
  "gallstone_found": false,
  "size_min": null,
  "size_max": null,
  "size_summation": null,
  "unit": null,
  "_note": "ไม่มีคีย์เวิร์ดเกี่ยวกับถุงน้ำดีใน Report"
}
```

---

## 🔄 วิธีการเปลี่ยนโมเดล (How to Change Model)

หากในอนาคตมีการอัปเดตไฟล์โมเดลเวอร์ชันใหม่ (ไฟล์ `.gguf`) ให้ทำตาม 3 ขั้นตอนนี้:

### ขั้นตอนที่ 1: ติดตั้งโมเดลตัวใหม่ลงใน Ollama
1. นำไฟล์โมเดลตัวใหม่ (เช่น `medgemma-v2.gguf`) ไปวางไว้ที่เดียวกับไฟล์ `Modelfile`
2. เปิดไฟล์ `Modelfile` ขึ้นมาแก้ไขบรรทัดแรกสุด ให้ชี้ไปที่ไฟล์ใหม่:
   ```text
   FROM ./medgemma-v2.gguf
   ```
3. เปิด PowerShell แล้วสั่งสร้างโมเดลชื่อใหม่ (เช่น ตั้งชื่อว่า `medgemma-v2`):
   ```powershell
   ollama create medgemma-v2 -f Modelfile
   ```

### ขั้นตอนที่ 2: เปลี่ยนชื่อโมเดลในโค้ด Backend
1. เปิดไฟล์ `backend/main.py`
2. ค้นหาบรรทัดที่ 10 (หรือใกล้เคียง): `MODEL_NAME = "medgemma-gallstone"`
3. แก้ชื่อในเครื่องหมายคำพูด เป็นชื่อโมเดลใหม่ที่เราเพิ่งตั้ง:
   ```python
   MODEL_NAME = "medgemma-v2"
   ```

### ขั้นตอนที่ 3: สั่งรีสตาร์ท Backend เพื่อให้โค้ดใหม่ทำงาน
1. เปิด PowerShell เข้าไปที่โฟลเดอร์ `backend`
2. รันคำสั่งนี้เพื่อให้ Docker อัปเดตโค้ดและสร้างระบบขึ้นมาใหม่:
   ```powershell
   docker-compose up -d --build
   ```

---

## 🛠️ วิธีการบำรุงรักษา (Maintenance)

- **หยุดการทำงานของ API:**
  ```powershell
  docker-compose down
  ```
- **ดู Log การทำงาน (เผื่อมี Error จาก SS):**
  ```powershell
  docker logs -f medgemma-api
  ```
- **หากต้องการแก้ไขโค้ด `main.py`:**
  แก้โค้ดเสร็จแล้ว ให้รัน `docker-compose up -d --build` ใหม่อีกครั้งเพื่อสร้างอิมเมจใหม่
