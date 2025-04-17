from db.connection import DatabaseConnection

class DatabaseQueries:
    def __init__(self):
        self.db = DatabaseConnection()

    def load_orders(self):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.OrderID, o.OrderNumber, o.BoxCount, o.ItemCount, o.CreatedDate
            FROM Orders o
            ORDER BY o.CreatedDate DESC
        ''')
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        return orders

    def load_boxes(self, order_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.BoxID, b.BoxNumber, 
                   CASE WHEN EXISTS (
                       SELECT 1 
                       FROM Items i 
                       WHERE i.BoxID = b.BoxID AND i.Scanned = 0
                   ) THEN 0 ELSE 1 END AS IsClosed,
                   b.IsDeferred
            FROM Boxes b
            WHERE b.OrderID = ?
        ''', (order_id,))
        boxes = cursor.fetchall()
        cursor.close()
        conn.close()
        return boxes

    def load_items(self, box_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ItemID, Barcode, ProductName, Size, Color, Scanned,
                   Composition, Country, ManufactureDate, Brand, Datamatrix, CryptoTail, Article
            FROM Items 
            WHERE BoxID = ?
        ''', (box_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return items

    def load_editor_items(self, order_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT i.ItemID, i.Barcode, i.ProductName, i.Size, i.Color
            FROM Items i
            JOIN Boxes b ON i.BoxID = b.BoxID
            WHERE b.OrderID = ?
        ''', (order_id,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return items

    def get_item_for_label(self, item_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT Barcode, ProductName, Article, Size, Color, Composition, Country, 
                   ManufactureDate, Brand, Datamatrix, CryptoTail
            FROM Items 
            WHERE ItemID = ?
        ''', (item_id,))
        item = cursor.fetchone()
        cursor.close()
        conn.close()
        return item

    def find_box(self, order_id, barcode):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT BoxID, BoxNumber, IsDeferred FROM Boxes WHERE OrderID = ? AND BoxNumber = ?", 
                      (order_id, barcode))
        box = cursor.fetchone()
        cursor.close()
        conn.close()
        return box

    def is_box_closed(self, box_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT CASE WHEN EXISTS (
                SELECT 1 
                FROM Items i 
                WHERE i.BoxID = ? AND i.Scanned = 0
            ) THEN 0 ELSE 1 END
        ''', (box_id,))
        is_closed = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return is_closed == 1

    def open_box(self, box_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE Boxes SET IsDeferred = 0 WHERE BoxID = ?", (box_id,))
        cursor.execute("UPDATE Items SET Scanned = 0 WHERE BoxID = ?", (box_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def scan_item(self, box_id, barcode):
        conn = self.db.connect()
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ItemID, Barcode, ProductName, Article, Size, Color, Scanned,
                   Composition, Country, ManufactureDate, Brand, Datamatrix, CryptoTail
            FROM Items 
            WHERE BoxID = ? AND Barcode = ? AND Scanned = 0
        ''', (box_id, barcode))
        item = cursor.fetchone()

        cursor.execute('''
            SELECT COUNT(*) 
            FROM Items 
            WHERE BoxID = ? AND Barcode = ?
        ''', (box_id, barcode))
        total_items = cursor.fetchone()[0]

        if item:
            cursor.execute("UPDATE Items SET Scanned = 1 WHERE ItemID = ?", (item[0],))

        cursor.close()
        conn.close()
        return item, total_items

    def get_unscanned_items_count(self, box_id):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Items WHERE BoxID = ? AND Scanned = 0", (box_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    def add_order(self, order_number, box_count, item_count):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Orders (OrderNumber, BoxCount, ItemCount) 
            VALUES (?, ?, ?)
        ''', (order_number, box_count, item_count))
        order_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]
        cursor.close()
        conn.close()
        return order_id

    def add_box(self, order_id, box_number):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Boxes (OrderID, BoxNumber) 
            VALUES (?, ?)
        ''', (order_id, box_number))
        box_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]
        cursor.close()
        conn.close()
        return box_id

    def add_item(self, box_id, item_data):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Items (BoxID, Barcode, Datamatrix, CryptoTail, ProductName, Article, Size, 
                              Color, Composition, Country, ManufactureDate, Brand, Scanned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (box_id, item_data['barcode'], item_data['datamatrix'], item_data['crypto_tail'], 
              item_data['product_name'], item_data['article'], item_data['size'], item_data['color'], 
              item_data['composition'], item_data['country'], item_data['manufacture_date'], 
              item_data['brand']))
        conn.commit()
        cursor.close()
        conn.close()
