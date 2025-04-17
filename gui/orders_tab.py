import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
from logic.xlsm_loader import XLSMLoader
from logic.printer import Printer
from db.queries import DatabaseQueries

class OrdersTab:
    def __init__(self, parent, theme_manager):
        self.frame = ttk.Frame(parent)
        self.db = DatabaseQueries()
        self.printer = Printer()
        self.xlsm_loader = XLSMLoader(self.db)

        self.queue = queue.Queue()
        self.current_box = None
        self.current_order_id = None
        self.scanned_items = set()

        self.orders_cache = None
        self.boxes_cache = {}
        self.items_cache = {}

        self.printers = self.printer.get_printers()
        self.no_print_var = tk.BooleanVar(value=False)
        self.selected_printer = tk.StringVar(value=self.printers[0] if self.printers else "Нет доступных принтеров")
        self.status_var = tk.StringVar(value="Готов")
        self.current_box_number_var = tk.StringVar(value="Короб не выбран")

        self.theme_manager = theme_manager

        self.setup_gui()
        self.load_orders()
        self.process_queue()

    def apply_theme(self):
        # Применяем тему к обоим Treeview: boxes_tree и items_tree
        self.theme_manager.apply_theme(self.theme_manager.get_current_theme(), self.boxes_tree)
        self.theme_manager.apply_theme(self.theme_manager.get_current_theme(), self.items_tree)

    def setup_gui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=3)
        self.frame.columnconfigure(2, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=0)
        self.frame.rowconfigure(2, weight=1)
        self.frame.rowconfigure(3, weight=0)

        # Панель сканирования
        scan_frame = ttk.LabelFrame(self.frame, text="Сканирование", padding="15", style='Scan.TLabelframe')
        scan_frame.grid(row=0, column=0, columnspan=3, pady=(15, 10), padx=15, sticky=(tk.W, tk.E))
        scan_frame.columnconfigure(0, weight=1)

        ttk.Label(scan_frame, text="Сканировать короб/товар:", font=("Helvetica", 14)).grid(row=0, column=0, pady=10)
        self.scan_entry = ttk.Entry(scan_frame, width=60, font=("Helvetica", 16))
        self.scan_entry.grid(row=1, column=0, padx=20, pady=10)
        self.scan_entry.bind("<Return>", self.process_scan)
        self.scan_entry.focus()

        # Верхняя панель с кнопками и статусом
        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=15, sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.X)

        ttk.Button(button_frame, text="Загрузить XLSM", command=self.load_xlsm_file, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отчет по заказу", command=self.generate_order_report, style='Accent.TButton').pack(side=tk.LEFT, padx=5)

        printer_frame = ttk.Frame(top_frame)
        printer_frame.pack(side=tk.RIGHT, fill=tk.X)

        ttk.Label(printer_frame, text="Принтер:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        printer_menu = ttk.Combobox(printer_frame, textvariable=self.selected_printer, values=self.printers, state="readonly", width=25, font=("Helvetica", 11))
        printer_menu.pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(printer_frame, text="Не печатать", variable=self.no_print_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(printer_frame, textvariable=self.status_var, font=("Helvetica", 12)).pack(side=tk.LEFT, padx=15)

        # Основной контент
        content_frame = ttk.Frame(self.frame)
        content_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=15)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=3)
        content_frame.columnconfigure(2, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Список заказов
        orders_frame = ttk.LabelFrame(content_frame, text="Заказы", padding="10", style='Section.TLabelframe')
        orders_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        self.orders_tree = ttk.Treeview(orders_frame, columns=("Заказ", "Коробки", "Товары", "Дата создания"), show="headings")
        self.orders_tree.heading("Заказ", text="Номер заказа")
        self.orders_tree.heading("Коробки", text="Кол-во коробок")
        self.orders_tree.heading("Товары", text="Кол-во товаров")
        self.orders_tree.heading("Дата создания", text="Дата создания")
        self.orders_tree.column("Заказ", width=180)
        self.orders_tree.column("Коробки", width=120)
        self.orders_tree.column("Товары", width=120)
        self.orders_tree.column("Дата создания", width=180)
        self.orders_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        orders_frame.columnconfigure(0, weight=1)
        orders_frame.rowconfigure(0, weight=1)
        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_select)

        # Список товаров
        items_frame = ttk.LabelFrame(content_frame, text="Товары", padding="10", style='Section.TLabelframe')
        items_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        box_number_label = ttk.Label(items_frame, textvariable=self.current_box_number_var, font=("Helvetica", 14, "bold"))
        box_number_label.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        self.items_tree = ttk.Treeview(items_frame, columns=("Штрихкод", "Товар", "Размер", "Цвет", "Статус"), show="headings")
        self.items_tree.heading("Штрихкод", text="Штрихкод")
        self.items_tree.heading("Товар", text="Товар")
        self.items_tree.heading("Размер", text="Размер")
        self.items_tree.heading("Цвет", text="Цвет")
        self.items_tree.heading("Статус", text="Статус")
        self.items_tree.column("Штрихкод", width=150)
        self.items_tree.column("Товар", width=200)
        self.items_tree.column("Размер", width=100)
        self.items_tree.column("Цвет", width=100)
        self.items_tree.column("Статус", width=120)
        self.items_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(1, weight=1)

        # Список коробов
        boxes_frame = ttk.LabelFrame(content_frame, text="Короба", padding="10", style='Section.TLabelframe')
        boxes_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        self.boxes_tree = ttk.Treeview(boxes_frame, columns=("Короб",), show="headings")
        self.boxes_tree.heading("Короб", text="Номер короба")
        self.boxes_tree.column("Короб", width=150)
        self.boxes_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        boxes_frame.columnconfigure(0, weight=1)
        boxes_frame.rowconfigure(0, weight=1)

        # Инициализация тегов для boxes_tree и items_tree
        self.apply_theme()

        # Кнопки снизу
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=15, padx=15)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.close_box_btn = ttk.Button(button_frame, text="Закрыть короб", command=self.close_box, state="disabled", style='Large.TButton')
        self.close_box_btn.grid(row=0, column=0, padx=10, sticky=tk.E)
        self.defer_box_btn = ttk.Button(button_frame, text="Отложить короб", command=self.defer_box, state="disabled", style='Large.TButton')
        self.defer_box_btn.grid(row=0, column=1, padx=10)
        self.add_item_btn = ttk.Button(button_frame, text="Добавить товар", command=self.add_item_to_box, state="disabled", style='Large.TButton')
        self.add_item_btn.grid(row=0, column=2, padx=10, sticky=tk.W)

    def process_queue(self):
        try:
            while True:
                task, data = self.queue.get_nowait()
                if task == "load_orders":
                    self.update_orders(data)
                elif task == "load_boxes":
                    self.update_boxes(data)
                elif task == "load_items":
                    self.update_items(data)
                elif task == "update_status":
                    self.update_scan_status(data)
                elif task == "close_box":
                    self.update_close_box(*data)
                elif task == "warning":
                    messagebox.showwarning("Предупреждение", data)
                elif task == "error":
                    messagebox.showerror("Ошибка", data)
                elif task == "message":
                    messagebox.showinfo("Информация", data)
                elif task == "status":
                    self.status_var.set(data)
        except queue.Empty:
            pass
        self.frame.after(100, self.process_queue)

    def update_orders(self, orders):
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        for row in orders:
            created_date = row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else ''
            self.orders_tree.insert("", "end", values=(row[1], row[2], row[3], created_date), tags=(row[0],))

    def update_boxes(self, boxes):
        for item in self.boxes_tree.get_children():
            self.boxes_tree.delete(item)
        for box in boxes:
            box_id, box_number, is_closed, is_deferred = box
            tags = []
            if is_closed:
                tags.append("closed")
            if is_deferred:
                tags.append("deferred")
            self.boxes_tree.insert("", "end", values=(box_number,), tags=tags + [box_id])

    def update_items(self, items):
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        for row in items:
            status = "Отсканирован" if row[5] else "Не отсканирован"
            tags = ["scanned"] if row[5] else []  # Добавляем тег "scanned", если товар отсканирован
            self.items_tree.insert("", "end", values=(row[1], row[2], row[3], row[4], status), tags=tags)

    def update_scan_status(self, data):
        item, barcode, total_items = data
        status = f"Отсканирован товар: {item[2]} (Штрихкод: {barcode}, Всего: {total_items})"
        self.status_var.set(status)
        self.scanned_items.add(item[0])
        self.load_items()

        if not self.no_print_var.get():
            item_data = {
                "{barcode}": str(item[1] or ""),
                "{product_name}": str(item[2] or ""),
                "{article}": str(item[12] or ""),
                "{size}": str(item[3] or ""),
                "{color}": str(item[4] or ""),
                "{composition}": str(item[6] or ""),
                "{country}": str(item[7] or ""),
                "{manufacture_date}": str(item[8] or ""),
                "{brand}": str(item[9] or ""),
                "{datamatrix}": str(item[10] or ""),
                "{crypto_tail}": str(item[11] or "")
            }
            self.printer.print_label_using_template(item_data, self.selected_printer.get(), self.no_print_var.get())

    def update_close_box(self, box_id, is_deferred):
        if self.current_order_id in self.boxes_cache:
            for i, (b_id, b_num, _, _) in enumerate(self.boxes_cache[self.current_order_id]):
                if b_id == box_id:
                    unscanned_items = self.db.get_unscanned_items_count(box_id)
                    if unscanned_items > 0 and not is_deferred:
                        self.queue.put(("warning", f"В коробе {b_num} осталось {unscanned_items} неотсканированных товаров!"))
                        return
                    self.boxes_cache[self.current_order_id][i] = (b_id, b_num, not is_deferred, is_deferred)
                    break

        self.current_box = None
        self.current_box_number_var.set("Короб не выбран")
        self.close_box_btn.config(state="disabled")
        self.defer_box_btn.config(state="disabled")
        self.add_item_btn.config(state="disabled")
        self.scanned_items.clear()
        self.load_boxes(self.current_order_id)

    def load_orders(self):
        if self.orders_cache is not None:
            self.update_orders(self.orders_cache)
        else:
            self.status_var.set("Загрузка заказов...")
            threading.Thread(target=self.load_orders_async, daemon=True).start()

    def load_orders_async(self):
        try:
            orders = self.db.load_orders()
            self.orders_cache = orders
            self.queue.put(("load_orders", orders))
            self.queue.put(("status", "Готов"))
        except Exception as e:
            self.queue.put(("error", f"Не удалось загрузить заказы: {str(e)}"))
            self.queue.put(("status", "Ошибка"))

    def on_order_select(self, event):
        selected_item = self.orders_tree.selection()
        if not selected_item:
            return
        self.current_order_id = self.orders_tree.item(selected_item, "tags")[0]
        self.current_box = None
        self.current_box_number_var.set("Короб не выбран")
        self.close_box_btn.config(state="disabled")
        self.defer_box_btn.config(state="disabled")
        self.add_item_btn.config(state="disabled")
        self.scanned_items.clear()
        self.load_boxes(self.current_order_id)

    def load_boxes(self, order_id):
        if order_id in self.boxes_cache:
            self.update_boxes(self.boxes_cache[order_id])
        else:
            self.status_var.set("Загрузка коробов...")
            threading.Thread(target=self.load_boxes_async, args=(order_id,), daemon=True).start()

    def load_boxes_async(self, order_id):
        try:
            boxes = self.db.load_boxes(order_id)
            self.boxes_cache[order_id] = boxes
            self.queue.put(("load_boxes", boxes))
            self.queue.put(("status", "Готов"))
        except Exception as e:
            self.queue.put(("error", f"Не удалось загрузить короба: {str(e)}"))
            self.queue.put(("status", "Ошибка"))

    def load_items(self):
        if self.current_box is None:
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)
            return
        if self.current_box in self.items_cache:
            self.update_items(self.items_cache[self.current_box])
        else:
            self.status_var.set("Загрузка товаров...")
            threading.Thread(target=self.load_items_async, daemon=True).start()

    def load_items_async(self):
        try:
            items = self.db.load_items(self.current_box)
            self.items_cache[self.current_box] = items
            self.queue.put(("load_items", items))
            self.queue.put(("status", "Готов"))
        except Exception as e:
            self.queue.put(("error", f"Не удалось загрузить товары: {str(e)}"))
            self.queue.put(("status", "Ошибка"))

    def process_scan(self, event):
        barcode = self.scan_entry.get().strip()
        if not barcode:
            return

        self.scan_entry.delete(0, tk.END)

        if not self.current_order_id:
            messagebox.showwarning("Предупреждение", "Сначала выберите заказ!")
            return

        if not self.current_box:
            try:
                box = self.db.find_box(self.current_order_id, barcode)
                if not box:
                    messagebox.showwarning("Предупреждение", f"Короб с номером {barcode} не найден в заказе!")
                    return

                box_id, box_number, is_deferred = box
                is_closed = self.db.is_box_closed(box_id)

                if is_closed or is_deferred:
                    if not self.prompt_password(box_id, box_number):
                        return
                    self.db.open_box(box_id)

                    if self.current_order_id in self.boxes_cache:
                        for i, (b_id, b_num, _, _) in enumerate(self.boxes_cache[self.current_order_id]):
                            if b_id == box_id:
                                self.boxes_cache[self.current_order_id][i] = (b_id, b_num, False, False)
                                break

                    if box_id in self.items_cache:
                        items = self.items_cache[box_id]
                        updated_items = []
                        for item in items:
                            updated_items.append((item[0], item[1], item[2], item[3], item[4], 0,
                                                 item[6], item[7], item[8], item[9], item[10], item[11], item[12]))
                        self.items_cache[box_id] = updated_items

                    self.load_boxes(self.current_order_id)

                self.current_box = box_id
                self.current_box_number_var.set(f"Короб {box_number}")
                self.close_box_btn.config(state="normal")
                self.defer_box_btn.config(state="normal")
                self.add_item_btn.config(state="normal")
                self.scanned_items.clear()
                self.load_items()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть короб: {str(e)}")
                return
        else:
            threading.Thread(target=self.process_scan_async, args=(barcode,), daemon=True).start()

    def process_scan_async(self, barcode):
        try:
            item, total_items = self.db.scan_item(self.current_box, barcode)
            if item:
                if self.current_box in self.items_cache:
                    for i, it in enumerate(self.items_cache[self.current_box]):
                        if it[0] == item[0]:
                            self.items_cache[self.current_box][i] = (
                                it[0], it[1], it[2], it[3], it[4], 1,
                                it[6], it[7], it[8], it[9], it[10], it[11], it[12]
                            )
                            break
                self.queue.put(("update_status", (item, barcode, total_items)))
            else:
                if total_items == 0:
                    self.queue.put(("warning", f"Товар с штрихкодом {barcode} не найден в этом коробе!"))
                else:
                    self.queue.put(("warning", f"Все товары с штрихкодом {barcode} уже отсканированы!"))
        except Exception as e:
            self.queue.put(("error", f"Ошибка при сканировании товара: {str(e)}"))

    def prompt_password(self, box_id, box_number):
        password_window = tk.Toplevel(self.frame)
        password_window.title(f"Введите пароль для короба {box_number}")
        password_window.geometry("350x200")
        password_window.transient(self.frame)
        password_window.grab_set()

        current_theme = self.theme_manager.get_current_theme()
        theme_colors = self.theme_manager.themes[current_theme]
        password_window.configure(bg=theme_colors["TFrame"]["background"])

        ttk.Label(password_window, text="Пароль:", font=("Helvetica", 14)).grid(row=0, column=0, padx=15, pady=15)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(password_window, textvariable=password_var, show="*", font=("Helvetica", 14), width=20)
        password_entry.grid(row=1, column=0, padx=15, pady=10)
        password_entry.focus()

        result = [False]

        def on_confirm():
            password = password_var.get()
            if password == "12345":
                result[0] = True
                password_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Неверный пароль!")
                password_entry.delete(0, tk.END)

        ttk.Button(password_window, text="Подтвердить", command=on_confirm, style='Accent.TButton').grid(row=2, column=0, pady=15)
        password_window.wait_window()
        return result[0]

    def close_box(self):
        if not self.current_box:
            return
        self.queue.put(("close_box", (self.current_box, False)))

    def defer_box(self):
        if not self.current_box:
            return
        self.queue.put(("close_box", (self.current_box, True)))

    def add_item_to_box(self):
        if not self.current_box:
            messagebox.showwarning("Предупреждение", "Сначала выберите короб!")
            return

        item_window = tk.Toplevel(self.frame)
        item_window.title("Добавить товар")
        item_window.geometry("450x600")
        item_window.transient(self.frame)
        item_window.grab_set()

        current_theme = self.theme_manager.get_current_theme()
        theme_colors = self.theme_manager.themes[current_theme]
        item_window.configure(bg=theme_colors["TFrame"]["background"])

        fields = {
            "barcode": ("Штрихкод", tk.StringVar()),
            "datamatrix": ("Datamatrix", tk.StringVar()),
            "crypto_tail": ("Криптохвост", tk.StringVar()),
            "product_name": ("Название товара", tk.StringVar()),
            "article": ("Артикул", tk.StringVar()),
            "size": ("Размер", tk.StringVar()),
            "color": ("Цвет", tk.StringVar()),
            "composition": ("Состав", tk.StringVar()),
            "country": ("Страна", tk.StringVar()),
            "manufacture_date": ("Дата производства", tk.StringVar()),
            "brand": ("Бренд", tk.StringVar())
        }

        row = 0
        for field, (label, var) in fields.items():
            ttk.Label(item_window, text=label + ":", font=("Helvetica", 12)).grid(row=row, column=0, padx=15, pady=8, sticky=tk.W)
            ttk.Entry(item_window, textvariable=var, font=("Helvetica", 12), width=30).grid(row=row, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            row += 1

        def on_confirm():
            item_data = {field: var.get() for field, (_, var) in fields.items()}
            self.db.add_item(self.current_box, item_data)
            self.load_items()
            item_window.destroy()

        ttk.Button(item_window, text="Добавить", command=on_confirm, style='Accent.TButton').grid(row=row, column=0, columnspan=2, pady=15)
        item_window.columnconfigure(1, weight=1)

    def load_xlsm_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XLSM файлы", "*.xlsm")])
        if not file_path:
            return
        self.status_var.set("Загрузка XLSM файла...")
        threading.Thread(target=self.xlsm_loader.load_xlsm, args=(file_path, self.queue), daemon=True).start()

    def generate_order_report(self):
        if not self.current_order_id:
            messagebox.showwarning("Предупреждение", "Сначала выберите заказ!")
            return
        self.status_var.set("Генерация отчета...")
        threading.Thread(target=self.printer.generate_order_report, 
                        args=(self.current_order_id, self.db, self.queue), daemon=True).start()