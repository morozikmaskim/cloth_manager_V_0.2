import pandas as pd
from datetime import datetime

class XLSMLoader:
    def __init__(self, db):
        self.db = db

    def load_xlsm(self, file_path, queue):
        try:
            df = pd.read_excel(file_path, sheet_name="Sheet1", engine="openpyxl")
            order_number = df.iloc[0]["OrderNumber"]
            box_count = int(df.iloc[0]["BoxCount"])
            item_count = len(df)

            order_id = self.db.add_order(order_number, box_count, item_count)

            current_box_number = None
            box_id = None
            for _, row in df.iterrows():
                box_number = row["BoxNumber"]
                if box_number != current_box_number:
                    box_id = self.db.add_box(order_id, box_number)
                    current_box_number = box_number

                item_data = {
                    "barcode": str(row["Barcode"]),
                    "datamatrix": str(row["Datamatrix"]),
                    "crypto_tail": str(row["CryptoTail"]),
                    "product_name": row["ProductName"],
                    "article": str(row["Article"]),
                    "size": row["Size"],
                    "color": row["Color"],
                    "composition": row["Composition"],
                    "country": row["Country"],
                    "manufacture_date": row["ManufactureDate"],
                    "brand": row["Brand"]
                }
                self.db.add_item(box_id, item_data)

            queue.put(("message", "XLSM файл успешно загружен!"))
            queue.put(("status", "Готов"))
        except Exception as e:
            queue.put(("error", f"Не удалось загрузить XLSM файл: {str(e)}"))
            queue.put(("status", "Ошибка"))
