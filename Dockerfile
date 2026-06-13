# Fed Tracker — full-stack (frontend + Python API) ในอิมเมจเดียว
# ใช้ stdlib ล้วน ไม่ต้องติดตั้ง dependency
FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Render/Railway/Fly จะส่งพอร์ตมาทาง env PORT
ENV PORT=8000
EXPOSE 8000

# (ไม่บังคับ) ใส่ FRED key ตอน deploy เพื่อให้ /api/rate ทำงานอัตโนมัติ
# ENV FRED_API_KEY=xxxxx

CMD ["python", "server.py"]
