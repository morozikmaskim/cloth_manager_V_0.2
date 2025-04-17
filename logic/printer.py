import win32print
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pylibdmtx.pylibdmtx import encode
from PIL import Image as PILImage
import tempfile

class Printer:
    def __init__(self):
        # Регистрация шрифтов
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        except Exception:
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
            except Exception:
                pass

    def get_printers(self):
        try:
            return [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except Exception:
            return []

    def generate_datamatrix_image(self, datamatrix_str):
        if not datamatrix_str:
            return None
        try:
            encoded = encode(datamatrix_str.encode('utf-8'))
            if not encoded:
                return None
            img = PILImage.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            img = img.convert('L')
            img = img.resize((100, 100), PILImage.Resampling.LANCZOS)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            return temp_file.name
        except Exception:
            return None

    def print_label_using_template(self, item_data, printer_name, no_print):
        try:
            with open("label_template.json", "r", encoding="utf-8") as f:
                import json
                template = json.load(f)
        except FileNotFoundError:
            raise Exception("Шаблон не найден! Сначала сохраните шаблон.")
        except Exception as e:
            raise Exception(f"Не удалось загрузить шаблон: {str(e)}")

        filename = f"label_{item_data['{barcode}']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=(template["width"], template["height"]))

        datamatrix_image_path = self.generate_datamatrix_image(item_data["{datamatrix}"])

        for obj in template["objects"]:
            x, y = obj["x"], template["height"] - obj["y"]
            if obj["type"] == "text":
                font_size = obj.get("font_size", 12)
                font_name = "DejaVuSans-Bold" if obj.get("bold", False) else "DejaVuSans"
                try:
                    c.setFont(font_name, font_size)
                except:
                    font_name = "Arial-Bold" if obj.get("bold", False) else "Arial"
                    c.setFont(font_name, font_size)

                text = obj["text"]
                if obj.get("is_custom", False):
                    c.drawString(x, y, text)
                else:
                    if text == "{datamatrix}":
                        if datamatrix_image_path:
                            c.drawImage(datamatrix_image_path, x, y - 100, width=100, height=100)
                    else:
                        if text in item_data:
                            text = item_data[text]
                        c.drawString(x, y, text)
            else:
                scale = obj.get("scale", 1.0)
                max_size = int(100 * scale)
                c.drawImage(obj["path"], x, y - max_size, width=max_size, height=max_size)

        c.showPage()
        c.save()

        if datamatrix_image_path and os.path.exists(datamatrix_image_path):
            os.unlink(datamatrix_image_path)

        if not no_print:
            try:
                win32print.SetDefaultPrinter(printer_name)
                os.startfile(filename, "print")
            except Exception as e:
                raise Exception(f"Ошибка печати: {str(e)}")
        else:
            return f"Этикетка сохранена как {filename}"

    def generate_order_report(self, order_id, db, queue):
        try:
            conn = db.db.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.OrderNumber, b.BoxNumber, i.Barcode, i.ProductName, i.Size, i.Color, i.Scanned
                FROM Orders o
                LEFT JOIN Boxes b ON o.OrderID = b.OrderID
                LEFT JOIN Items i ON b.BoxID = i.BoxID
                WHERE o.OrderID = ?
            ''', (order_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            filename = f"order_report_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            c = canvas.Canvas(filename, pagesize=A4)
            y = 800
            c.setFont("DejaVuSans", 12)

            for row in rows:
                if y < 50:
                    c.showPage()
                    y = 800
                text = f"Заказ: {row[0]}, Короб: {row[1]}, Товар: {row[3]}, Штрихкод: {row[2]}, Размер: {row[4]}, Цвет: {row[5]}, Статус: {'Отсканирован' if row[6] else 'Не отсканирован'}"
                c.drawString(50, y, text)
                y -= 20

            c.showPage()
            c.save()
            queue.put(("message", f"Отчет сохранен как {filename}"))
            queue.put(("status", "Готов"))
        except Exception as e:
            queue.put(("error", f"Не удалось сгенерировать отчет: {str(e)}"))
            queue.put(("status", "Ошибка"))
