# ของดีมีต่อ — เว็บซื้อขายของมือสอง (Django)

## ฟีเจอร์
- **Authentication**: สมัครสมาชิก / เข้าสู่ระบบ / ออกจากระบบ / รีเซ็ตรหัสผ่านทางอีเมล
- **CRUD สินค้า**: ลงขาย (Create), ดูรายการ/รายละเอียด (Read), แก้ไข (Update), ลบ (Delete) — แก้/ลบได้เฉพาะเจ้าของสินค้า
- **สั่งซื้อ**: กรอกที่อยู่จัดส่ง, กันซื้อซ้ำด้วย transaction, ซื้อสินค้าตัวเองไม่ได้
- **ติดตามคำสั่งซื้อ**: ผู้ขายกด "ยืนยันจัดส่งแล้ว" → ผู้ซื้อกด "ได้รับของแล้ว"
- **ค้นหา + กรองหมวดหมู่ + แบ่งหน้า**
- **แดชบอร์ดผู้ขาย** แสดงกราฟ Chart.js (ยอดขายรายเดือน, สินค้าตามหมวดหมู่)

## วิธีรัน
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations shop
python manage.py migrate
python manage.py createsuperuser   # (ไม่บังคับ) สำหรับเข้า /admin/
python manage.py runserver
```
เปิด http://127.0.0.1:8000/

> **ถ้าเคยรันเวอร์ชันก่อนหน้าแล้วมีไฟล์ `db.sqlite3` เดิม**: ฟิลด์ใหม่ของสินค้า (หมวดหมู่ / สภาพ / ต่อรองได้) ต้องสร้าง migration เพิ่ม
> ให้รัน `python manage.py makemigrations shop` แล้ว `python manage.py migrate` อีกครั้ง
> (ถ้าไม่มีข้อมูลสำคัญ ลบ `db.sqlite3` และโฟลเดอร์ `shop/migrations/` ทิ้งแล้วเริ่มใหม่ก็ได้)

## ทดสอบรีเซ็ตรหัสผ่าน
ตอนพัฒนาระบบตั้ง `EMAIL_BACKEND` เป็น console — เมื่อกด "ลืมรหัสผ่าน?" **อีเมลจะแสดงใน terminal ที่รัน `runserver`**
ให้คัดลอกลิงก์ในอีเมลไปเปิดในเบราว์เซอร์เพื่อตั้งรหัสผ่านใหม่ (ต้องใช้อีเมลที่กรอกตอนสมัครสมาชิก)

## หมายเหตุ
- ต้องใช้อินเทอร์เน็ต (โหลด Tailwind CSS, Chart.js และฟอนต์จาก CDN)
- ก่อนขึ้นเซิร์ฟเวอร์จริง: เปลี่ยน SECRET_KEY, ตั้ง DEBUG=False และ ALLOWED_HOSTS, เปลี่ยน EMAIL_BACKEND เป็น SMTP
