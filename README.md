# Fed Tracker 🪙

เว็บติดตามทิศทางดอกเบี้ยธนาคารกลางสหรัฐฯ (Fed) — รวม **FedWatch**, **Dot Plot**,
**Fed Funds Rate** และกราฟเปรียบเทียบ **Fed vs ตลาด** ไว้ในหน้าเดียว

- ตอบคำถาม: Fed จะ **ขึ้น/ลด** ดอกเบี้ย **เมื่อไหร่** และ **เท่าไหร่** (โอกาสเป็น %)
- Frontend เป็น static ล้วน (HTML/CSS/JS วาดกราฟ SVG เอง ไม่มี dependency)
- Backend เป็น Python **standard library ล้วน** — ไม่ต้อง `pip install` อะไรเลย

---

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|------|---------|
| `index.html` `styles.css` `app.js` | Frontend |
| `data.js` | ข้อมูลตัวอย่าง + Dot Plot (Dot Plot ต้องอัปเดตมือจาก Fed SEP) |
| `fedwatch.py` | คำนวณ FedWatch จาก Fed Funds futures (วิธี CME) |
| `server.py` | เว็บเซิร์ฟเวอร์ + REST API (`/api/fedwatch`, `/api/rate`) |
| `futures_prices.json` | ราคา futures สำรอง (ใช้เมื่อดึง Yahoo ไม่ได้) |
| `Dockerfile` `render.yaml` | สำหรับ deploy แบบ full-stack |
| `.github/workflows/update-data.yml` | อัปเดต `live_data.json` อัตโนมัติ (สำหรับ static hosting) |

**ลำดับการหาข้อมูลของ frontend:** `/api/fedwatch` (backend) → `live_data.json` (generate ไว้) → ข้อมูลตัวอย่างใน `data.js`
มี badge มุมบนซ้ายบอกว่าตอนนี้ใช้ข้อมูลแบบไหน (LIVE / ตัวอย่าง)

---

## รันบนเครื่อง

### แบบเต็ม (มี FedWatch สด) — แนะนำ
```bash
python server.py
# เปิด http://localhost:8000
```
เซิร์ฟเวอร์จะดึงราคา Fed Funds futures จาก Yahoo มาคำนวณ FedWatch ให้ (cache 10 นาที)
ถ้า Yahoo โดน block จะใช้ราคาใน `futures_prices.json` แทน

### ทดสอบการคำนวณอย่างเดียว
```bash
python fedwatch.py             # พิมพ์ payload ออกมาดู
python fedwatch.py --write     # เขียนผลลง live_data.json
```

### แบบ static อย่างเดียว
เปิด `index.html` ผ่าน static server ใดก็ได้ (เช่น `python -m http.server`) — จะใช้ข้อมูลตัวอย่าง
หรือข้อมูลใน `live_data.json` ถ้ามี

---

## Fed Funds Rate สด (FRED)

ขอ API key ฟรีที่ <https://fred.stlouisfed.org/docs/api/api_key.html>

- **มี backend:** ใส่ key ในช่องมุมขวาบน กด "ดึงดอกเบี้ยสด" → เรียกผ่าน `/api/rate` (ไม่ติด CORS)
  หรือตั้ง env `FRED_API_KEY` ให้ดึงอัตโนมัติตั้งแต่ตอนโหลด
- **static อย่างเดียว:** จะยิงตรงไป FRED ซึ่ง**อาจติด CORS** — แนะนำให้รันผ่าน backend

---

## Deploy

### ตัวเลือก A — Full-stack (มี FedWatch สด) บน Render / Railway / Fly
มี `Dockerfile` พร้อมใช้ และ `render.yaml` สำหรับ Render:
1. push repo ขึ้น GitHub
2. Render → **New > Blueprint** → เลือก repo (อ่าน `render.yaml` อัตโนมัติ)
3. (ไม่บังคับ) ใส่ env `FRED_API_KEY`
> Railway/Fly: ใช้ `Dockerfile` ได้ตรงๆ — เซิร์ฟเวอร์อ่านพอร์ตจาก env `PORT`

### ตัวเลือก B — Static (ฟรี, ไม่มี backend) บน GitHub Pages / Netlify / Vercel
1. push repo → เปิด **GitHub Pages** (Settings > Pages > branch `main`)
2. ตั้ง secret `FRED_API_KEY` (ไม่บังคับ) ที่ Settings > Secrets
3. GitHub Action (`update-data.yml`) จะคำนวณ FedWatch แล้ว commit `live_data.json`
   ทุกวันทำการ — เว็บจะโหลดไฟล์นี้เป็นข้อมูลสด

| | FedWatch สด | Fed Funds Rate สด | ค่าใช้จ่าย |
|---|---|---|---|
| A. Full-stack | ✅ ทุกครั้งที่โหลด | ✅ | server เล็กๆ |
| B. Static | ✅ อัปเดตวันละครั้ง | ⚠️ ติด CORS | ฟรี |

---

## ⚠️ หมายเหตุเรื่องข้อมูล

- **FedWatch** คำนวณตามวิธี CME แบบ *simplified* (สมมติแต่ละประชุมขยับ ≤ 1 step,
  แล้ว convolve) — ทิศทางตรงกับ CME แต่ตัวเลขอาจต่างกันเล็กน้อย
- **Dot Plot** มาจาก Fed SEP (ออกไตรมาสละครั้ง) — **ต้องอัปเดตมือ**ใน `data.js` ที่ `FedData.dotPlot`
  เพราะไม่มี API สาธารณะ
- ใช้เพื่อการศึกษา/ติดตามเท่านั้น ไม่ใช่คำแนะนำการลงทุน

แหล่งข้อมูลจริง: [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) ·
[Fed SEP](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) ·
[FRED](https://fred.stlouisfed.org/)
