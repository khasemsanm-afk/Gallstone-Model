# 🏥 MedGemma Gallstone: Workflow & Architecture (สำหรับนำเสนอผู้บริหาร)

เอกสารฉบับนี้จัดทำขึ้นเพื่อแสดง **ผังการทำงาน (Workflow)** และ **ความพร้อมของระบบ (Feasibility)** ของโปรเจกต์ AI สกัดข้อมูลนิ่วในถุงน้ำดี ว่าสามารถนำไปใช้งานจริงร่วมกับระบบ SS ของโรงพยาบาลได้อย่างมีประสิทธิภาพ

---

## 1. 🏗️ สถาปัตยกรรมระบบ (System Architecture)

ระบบถูกออกแบบให้ **แยกส่วนการทำงาน** เพื่อไม่ให้ดึงทรัพยากรกัน และเพื่อให้ง่ายต่อการบำรุงรักษา

```mermaid
flowchart LR
    SS[Hospital System SS] <-->|HTTP POST :8000| Docker
    subgraph Docker ["Docker Environment (พนักงานรับแขก)"]
        API[FastAPI Container]
    end
    subgraph Windows ["Windows Host Machine (ผู้เชี่ยวชาญ)"]
        OLL[Ollama Service]
    end
    API <-->|host.docker.internal:11434| OLL
```



**จุดเด่น:**

- **Plug & Play:** ระบบ SS แค่ส่งข้อมูลมาทาง HTTP (เสมือนการเข้าเว็บไซต์) ไม่ต้องติดตั้ง AI ลงในระบบ SS เลย
- **No GPU Required:** ตัว AI ทำงานบน CPU ของเครื่อง Host ผ่าน Ollama ได้อย่างมีประสิทธิภาพ

---



## 2. 🧠 ลอจิกการทำงานของระบบ (Logic Flow)

กระบวนการตั้งแต่รับข้อมูลจากแพทย์ จนถึงการส่งคำตอบกลับไปยังระบบ

```mermaid
flowchart TD
    A[ระบบ SS ส่งประวัติคนไข้] -->|HTTP POST| B(Backend API)
    
    subgraph Backend [Docker: API Server]
        B --> C{ตรวจสอบด่านแรก:<br>มีคีย์เวิร์ดถุงน้ำดีไหม?}
        C -->|ไม่มี| D[ปัดตกทันที]
        C -->|มี| E[หั่นและคัดเฉพาะประโยคที่สำคัญ]
    end
    
    subgraph AIEngine [Windows Host: Ollama]
        E -->|ส่งข้อความที่สกัดแล้ว| F((MedGemma AI))
        F -->|ประมวลผล 2-5 วิ| G[วิเคราะห์และแยกขนาดนิ่ว]
    end
    
    D -->|gallstone_found: false| H[ส่ง JSON กลับไปที่ระบบ SS]
    G -->|gallstone_found: true| H
```



