# 🍎 Fruit Box

เกมลากกรอบเลือกแอปเปิลให้ผลรวมได้ **10 พอดี** ภายใน 120 วินาที — Python + pygame-ce

![Gameplay](docs/screenshots/gameplay.png)

| Menu | Settings | Game Over |
|---|---|---|
| ![Menu](docs/screenshots/menu.png) | ![Settings](docs/screenshots/settings.png) | ![Game Over](docs/screenshots/gameover.png) |

## ดาวน์โหลด
Windows: โหลด **FruitBox.exe** จาก [Releases](../../releases/latest) แล้วดับเบิลคลิกเล่นได้เลย

## วิธีเล่น
- กดเมาส์ค้างแล้วลากกรอบคลุมแอปเปิล ถ้ารวมได้ 10 แอปเปิลจะหายไป ได้คะแนนตามจำนวนลูก
- หมดเวลาแล้วกด **Continue** เพื่อเล่นกระดานเดิมต่อแบบไม่จำกัดเวลา (High Score นับเฉพาะ 120 วินาทีแรก)
- `ESC` กลับเมนู · `M` เปิด/ปิดเสียง · `F11` เต็มจอ · ปรับระดับเสียงได้ในหน้า **Settings**

## รันจากซอร์ส / Build
```bash
pip install -r requirements.txt
python main.py
```
Build เป็น `.exe` ไฟล์เดียว: รัน `build.bat` → ได้ `dist\FruitBox.exe`

## เครดิต
ฟอนต์ Lilita One และ Varela Round (SIL OFL) จาก Google Fonts · เสียงทั้งหมดสังเคราะห์ด้วย `tools/make_assets.py`
