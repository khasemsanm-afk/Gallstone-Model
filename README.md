# MedGemma Gallstone AI Project

ระบบ AI (MedGemma) สำหรับการสกัดข้อมูลนิ่วในถุงน้ำดีจากข้อความทางการแพทย์ (Ultrasound Reports) อัตโนมัติให้ออกมาเป็นรูปแบบ JSON ด้วยการแบ่งสถาปัตยกรรมการทำงานออกเป็น 2 ส่วนหลัก:
1. **API Server (Backend):** ทำงานบน Docker Container (FastAPI) มีหน้าที่รับคำขอ (Request), คัดกรองข้อมูล, และจัดรูปแบบคำตอบ (Response)
2. **AI Engine:** ทำงานแบบ Native บนเครื่อง Host ผ่าน Ollama
---

## สถาปัตยกรรมระบบ (Architecture)
การแยกส่วน API Server และ AI Engine ออกจากกัน เพื่อป้องกันไม่ให้ Docker ใช้ทรัพยากร RAM ร่วมกับตัวรัน AI และช่วยเพิ่มประสิทธิภาพ CPU ให้สามารถประมวลผลข้อมูล AI ได้รวดเร็วที่สุด

```mermaid
flowchart LR
    SS[Hospital System] <-->|HTTP POST :8000| Docker
    subgraph Docker ["Docker Environment"]
        API[FastAPI Container]
    end
    subgraph Windows ["Windows Host Machine"]
        OLL[Ollama Service]
    end
    API <-->|host.docker.internal:11434| OLL
```

---

## การรองรับระบบปฏิบัติการ (OS Compatibility & Network Settings)

โปรเจกต์นี้รองรับการทำงานบน **Windows, macOS และ Linux** แต่เนื่องจากระบบเครือข่ายของ Docker ทำงานแตกต่างกันในแต่ละ OS จึงต้องตั้งค่า `docker-compose.yml` และ `backend/main.py` ให้ตรงกับ OS ที่ใช้รัน Server ดังนี้:

### กรณีรันบน Windows หรือ macOS (ค่าเริ่มต้นของโค้ดบน GitHub)
Docker Desktop จะทำงานผ่าน Virtual Machine (VM) ทำให้ต้องใช้คำสั่งพิเศษเพื่อให้ Docker ทะลุกำแพงออกมาหา Ollama ที่อยู่บน Host เครื่องหลัก
*   **ไฟล์ `backend/main.py`:** ใช้ `OLLAMA_URL = "http://host.docker.internal:11434/api/generate"`
*   **ไฟล์ `docker-compose.yml`:**
    ```yaml
    services:
      api:
        ports:
          - "8000:8000"
        extra_hosts:
          - "host.docker.internal:host-gateway"
    ```

### กรณีรันบน Linux Server (เช่น Ubuntu, CentOS) 🐧
Linux รองรับฟีเจอร์ `network_mode: "host"` ของ Docker อย่างสมบูรณ์แบบ ซึ่งจะช่วยทลายกำแพงเครือข่ายทิ้ง ทำให้ Docker เชื่อมต่อกับ Ollama (Localhost) และระบบเครือข่ายของ Server (VPN/Intranet) ได้ตรงไปตรงมาที่สุด
*   **ไฟล์ `backend/main.py`:** ใช้ `OLLAMA_URL = "http://localhost:11434/api/generate"`
*   **ไฟล์ `docker-compose.yml`:** ลบ `ports` และ `extra_hosts` ทิ้ง แล้วใช้ `network_mode: "host"` แทน
    ```yaml
    services:
      api:
        network_mode: "host"
        command: uvicorn main:app --host 0.0.0.0 --port 8001  # (สามารถกำหนดพอร์ตที่ต้องการได้ ป้องกันการชนกับพอร์ตเดิมของระบบโรงพยาบาล)
    ```
*   **การอนุญาตสิทธิ์:** บน Linux คำสั่ง Docker จะต้องใช้ `sudo docker compose up -d --build` ในการเริ่มต้นระบบ
*   **การตั้งค่า Ollama (บน Linux):** หากพบปัญหา Connection Timeout ต้องเปิดให้ Ollama รับ Connection จากภายนอก โดยเพิ่ม `Environment="OLLAMA_HOST=0.0.0.0"` ในไฟล์ `/etc/systemd/system/ollama.service` แล้วรีสตาร์ท Ollama

---

## คู่มือการติดตั้งระบบ (Setup Guide)

### ขั้นที่ 1: เตรียมไฟล์ AI Model (GGUF)
ระบบต้องใช้ไฟล์โมเดลที่ผ่านการ Fine-tune เรียบร้อยแล้ว (เช่น `medgemma-1.5-4b-it.Q4_K_M.gguf` ขนาดประมาณ 2.5 GB)
*หมายเหตุ: ไฟล์โมเดลไม่มีใน GitHub เนื่องจากมีขนาดใหญ่เกินข้อจำกัด สามารถเข้าไปในลิงค์เพื่อโหลดไฟล์โมเดล https://drive.google.com/drive/u/1/folders/1v57ZY-MVtR0z-LVzyYsq0kZrt8pN0ZfG ถ้าไม่ได้กรุณาติดต่อผู้ดูแลโปรเจกต์เพื่อขอรับไฟล์* 
ให้นำไฟล์ที่ได้รับมาวางไว้ในโฟลเดอร์ Root ของโปรเจกต์

### ขั้นที่ 2: ติดตั้งโปรแกรม Ollama (สำหรับรัน AI ด้วย CPU)
1. ดาวน์โหลดโปรแกรมจาก: https://ollama.com/download
2. ดำเนินการติดตั้งสำหรับระบบปฏิบัติการ Windows ตามปกติ

### ขั้นที่ 3: นำเข้า AI Model สู่ระบบ Ollama
1. ตรวจสอบให้แน่ใจว่าไฟล์ `Modelfile` (ที่มีอยู่ในโปรเจกต์นี้) อยู่ในโฟลเดอร์เดียวกับไฟล์โมเดล GGUF
2. เปิด PowerShell และนำทาง (cd) ไปยังโฟลเดอร์ดังกล่าว
3. รันคำสั่งต่อไปนี้เพื่อนำเข้าโมเดลเข้าสู่ระบบ Ollama:
   ```powershell
   ollama create medgemma-gallstone -f Modelfile
   ```

### ขั้นที่ 4: เปิดระบบ Backend API (Docker)
1. ติดตั้ง Docker Desktop สำหรับ Windows
2. เปิด PowerShell และนำทางไปยังโฟลเดอร์ `backend`:
   ```powershell
   cd backend
   ```
3. รันคำสั่งสร้างและเปิด Backend Container:
   ```powershell
   docker-compose up -d --build
   ```
*(ตรวจสอบความพร้อมของระบบได้ที่: `http://localhost:8001/health`)*
*(สามารถทดสอบการเรียกใช้งาน API ผ่าน Swagger UI ได้ที่: `http://localhost:8001/docs`)*

---

## คู่มือเชื่อมต่อ API (API Connection Guide)

ระบบสื่อสารด้วย JSON ผ่านโพรโทคอล HTTP POST แบบ Synchronous 

### Endpoint: `/api/extract-gallstone`
- **Method:** `POST`
- **URL:** `http://<IP-Address>:8001/api/extract-gallstone` (หากเรียกจากเครื่องเดียวกันใช้ `localhost:8001`)
- **Content-Type:** `application/json`

#### Request Payload (ขาเข้า)
```json
{
  "raw_text": "Evidence: The gallbladder is distended and contains multiple small gallstones, size up to 1.5 cm..."
}
```

#### Response (ขาออก - กรณีพบข้อมูลนิ่ว)
```json
{
  "gallstone_found": true,
  "size_min": null,
  "size_max": 1.5,
  "size_summation": null,
  "unit": "cm"
}
```

#### Response (ขาออก - กรณีไม่พบคำสำคัญที่เกี่ยวข้องกับถุงน้ำดี)
ระบบจะทำการตรวจสอบคำสำคัญ (Keyword filtering) หากไม่พบคำที่เกี่ยวข้อง ระบบจะไม่ส่งข้อความต่อไปยัง AI Engine เพื่อประหยัดทรัพยากร และจะตอบกลับทันทีดังนี้:
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

## วิธีการเปลี่ยนหรืออัปเดตโมเดล (How to Update Model)

หากมีการอัปเดตไฟล์โมเดลเวอร์ชันใหม่ (เช่น เวอร์ชัน v2) ให้ปฏิบัติตาม 3 ขั้นตอนดังนี้:

1. **ติดตั้งโมเดลตัวใหม่ลงใน Ollama:**
   นำไฟล์ `.gguf` เวอร์ชันใหม่มาวาง แก้ไขไฟล์ `Modelfile` ให้บรรทัด `FROM` ระบุชื่อไฟล์ใหม่ และรันคำสั่งสร้างชื่อโมเดลใหม่:
   ```powershell
   ollama create medgemma-v2 -f Modelfile
   ```
2. **เปลี่ยนชื่อโมเดลในโค้ด Backend:**
   เปิดไฟล์ `backend/main.py` ค้นหาบรรทัด `MODEL_NAME = "medgemma-gallstone"` แล้วแก้ไขเป็นชื่อโมเดลใหม่ (`medgemma-v2`)
3. **รีสตาร์ท Backend:**
   นำทางไปยังโฟลเดอร์ `backend` แล้วรันคำสั่งเพื่อให้ Docker บิลด์อิมเมจใหม่ด้วยโค้ดล่าสุด:
   ```powershell
   docker-compose up -d --build
   ```

---

## การบำรุงรักษาและปัญหาที่พบบ่อย (Maintenance & Troubleshooting)

- **การหยุดการทำงานของ API:** รันคำสั่ง `docker-compose down` ในโฟลเดอร์ backend
- **การตรวจสอบ Log ของระบบ:** รันคำสั่ง `docker logs -f medgemma-api`
- **ปัญหาการเชื่อมต่อ API จากเครื่องอื่น:** ให้ตรวจสอบ Windows Defender Firewall ในเครื่องที่เปิดใช้งาน AI ว่ามีการอนุญาต (Inbound Rule) ให้เข้าถึงพอร์ต 8000 ได้หรือไม่
