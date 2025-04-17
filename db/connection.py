import pyodbc
from config.config import ConfigManager

class DatabaseConnection:
    def __init__(self):
        config = ConfigManager()
        self.connection_string = config.get_connection_string()

    def connect(self):
        conn = pyodbc.connect(self.connection_string)
        conn.autocommit = True
        return conn

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Orders')
            CREATE TABLE Orders (
                OrderID INT PRIMARY KEY IDENTITY(1,1),
                OrderNumber NVARCHAR(50),
                BoxCount INT,
                ItemCount INT,
                CreatedDate DATETIME DEFAULT GETDATE()
            )
        ''')
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Boxes')
            CREATE TABLE Boxes (
                BoxID INT PRIMARY KEY IDENTITY(1,1),
                OrderID INT,
                BoxNumber NVARCHAR(50),
                IsDeferred BIT DEFAULT 0,
                FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
            )
        ''')
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Items')
            CREATE TABLE Items (
                ItemID INT PRIMARY KEY IDENTITY(1,1),
                BoxID INT,
                Barcode NVARCHAR(100),
                Datamatrix NVARCHAR(100),
                CryptoTail NVARCHAR(100),
                ProductName NVARCHAR(100),
                Article NVARCHAR(100),
                Size NVARCHAR(20),
                Color NVARCHAR(50),
                Composition NVARCHAR(200),
                Country NVARCHAR(100),
                ManufactureDate NVARCHAR(50),
                Brand NVARCHAR(100),
                Scanned BIT DEFAULT 0,
                FOREIGN KEY (BoxID) REFERENCES Boxes(BoxID)
            )
        ''')
        cursor.close()
        conn.close()

    def create_indexes(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            IF NOT EXISTS (
                SELECT * FROM sys.indexes 
                WHERE name = 'IX_Boxes_OrderID' AND object_id = OBJECT_ID('Boxes')
            )
            CREATE INDEX IX_Boxes_OrderID ON Boxes(OrderID)
        ''')
        cursor.execute('''
            IF NOT EXISTS (
                SELECT * FROM sys.indexes 
                WHERE name = 'IX_Items_BoxID' AND object_id = OBJECT_ID('Items')
            )
            CREATE INDEX IX_Items_BoxID ON Items(BoxID)
        ''')
        cursor.execute('''
            IF NOT EXISTS (
                SELECT * FROM sys.indexes 
                WHERE name = 'IX_Items_Barcode' AND object_id = OBJECT_ID('Items')
            )
            CREATE INDEX IX_Items_Barcode ON Items(Barcode)
        ''')
        cursor.execute('''
            IF NOT EXISTS (
                SELECT * FROM sys.indexes 
                WHERE name = 'IX_Items_Scanned' AND object_id = OBJECT_ID('Items')
            )
            CREATE INDEX IX_Items_Scanned ON Items(Scanned)
        ''')
        cursor.close()
        conn.close()