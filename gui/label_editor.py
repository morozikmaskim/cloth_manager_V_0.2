import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image as PILImage, ImageTk
import os
import threading
import queue
from logic.label_template import LabelTemplate
from logic.printer import Printer
from db.queries import DatabaseQueries

class LabelEditorTab:
    def __init__(self, parent, theme_manager):
        self.frame = ttk.Frame(parent)
        self.db = DatabaseQueries()
        self.label_template = LabelTemplate()
        self.printer = Printer()

        self.queue = queue.Queue()
        self.orders_cache = None
        self.current_order_id = None

        self.label_objects = []
        self.scale = 4.0
        self.selected_object = None
        self.start_x = None
        self.start_y = None

        self.printers = self.printer.get_printers()
        self.selected_printer = tk.StringVar(value=self.printers[0] if self.printers else "Нет доступных принтеров")
        self.no_print_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Готов")
        self.scale_var = tk.StringVar(value=str(self.scale))

        self.theme_manager = theme_manager

        self.order_fields = [
            "{barcode}", "{product_name}", "{article}", "{size}", "{color}",
            "{composition}", "{country}", "{manufacture_date}", "{brand}",
            "{datamatrix}", "{crypto_tail}"
        ]
        self.selected_order_field = tk.StringVar(value=self.order_fields[0])

        self.setup_gui()
        self.load_editor_orders()
        self.process_queue()

    def apply_theme(self):
        self.theme_manager.apply_theme(self.theme_manager.get_current_theme())
        current_theme = self.theme_manager.get_current_theme()
        theme_colors = self.theme_manager.themes[current_theme]
        self.label_canvas.configure(
            background=theme_colors["TFrame"]["background"],
            highlightbackground=theme_colors["Treeview"]["background"]
        )
        # Применяем цвета к линейкам (h_ruler и v_ruler)
        self.h_ruler.configure(
            background=theme_colors["TFrame"]["background"],
            highlightbackground=theme_colors["Treeview"]["background"]
        )
        self.v_ruler.configure(
            background=theme_colors["TFrame"]["background"],
            highlightbackground=theme_colors["Treeview"]["background"]
        )
        self.corner_canvas.configure(
            background=theme_colors["TFrame"]["background"],
            highlightbackground=theme_colors["Treeview"]["background"]
        )

    def setup_gui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=3)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=0)
        self.frame.rowconfigure(2, weight=1)

        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=0, column=0, columnspan=2, pady=15, padx=15, sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.X)

        ttk.Button(button_frame, text="Добавить текст", command=self.add_text, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Добавить изображение", command=self.add_image, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сохранить шаблон", command=self.save_template, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить шаблон", command=self.clear_template, style='Accent.TButton').pack(side=tk.LEFT, padx=5)

        scale_frame = ttk.Frame(top_frame)
        scale_frame.pack(side=tk.LEFT, padx=15)
        ttk.Label(scale_frame, text="Масштаб:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        ttk.Button(scale_frame, text="−", command=self.decrease_scale, style='Accent.TButton', width=3).pack(side=tk.LEFT, padx=5)
        ttk.Label(scale_frame, textvariable=self.scale_var, font=("Helvetica", 12), width=5).pack(side=tk.LEFT, padx=5)
        ttk.Button(scale_frame, text="+", command=self.increase_scale, style='Accent.TButton', width=3).pack(side=tk.LEFT, padx=5)

        printer_frame = ttk.Frame(top_frame)
        printer_frame.pack(side=tk.RIGHT, fill=tk.X)

        ttk.Label(printer_frame, text="Принтер:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        printer_menu = ttk.Combobox(printer_frame, textvariable=self.selected_printer, values=self.printers, state="readonly", width=25, font=("Helvetica", 11))
        printer_menu.pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(printer_frame, text="Не печатать", variable=self.no_print_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(printer_frame, textvariable=self.status_var, font=("Helvetica", 12)).pack(side=tk.LEFT, padx=15)

        size_frame = ttk.LabelFrame(self.frame, text="Размеры этикетки (мм)", padding="15", style='Section.TLabelframe')
        size_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=15, sticky=(tk.W, tk.E))

        ttk.Label(size_frame, text="Ширина:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10)
        self.width_var = tk.StringVar(value="100")
        ttk.Entry(size_frame, textvariable=self.width_var, width=12, font=("Helvetica", 12)).grid(row=0, column=1, padx=10)

        ttk.Label(size_frame, text="Высота:", font=("Helvetica", 12)).grid(row=0, column=2, padx=10)
        self.height_var = tk.StringVar(value="50")
        ttk.Entry(size_frame, textvariable=self.height_var, width=12, font=("Helvetica", 12)).grid(row=0, column=3, padx=10)

        ttk.Button(size_frame, text="Применить", command=self.update_label_size, style='Accent.TButton').grid(row=0, column=4, padx=10)

        content_frame = ttk.Frame(self.frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=15)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=3)
        content_frame.rowconfigure(0, weight=1)

        editor_frame = ttk.LabelFrame(content_frame, text="Редактор", padding="15", style='Section.TLabelframe')
        editor_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        canvas_container = ttk.Frame(editor_frame)
        canvas_container.grid(row=0, column=0, padx=10, pady=10)

        self.corner_canvas = tk.Canvas(canvas_container, width=30, height=30, highlightthickness=0)
        self.corner_canvas.grid(row=0, column=0)

        self.h_ruler = tk.Canvas(canvas_container, width=600, height=30, highlightthickness=0)
        self.h_ruler.grid(row=0, column=1)

        self.v_ruler = tk.Canvas(canvas_container, width=30, height=300, highlightthickness=0)
        self.v_ruler.grid(row=1, column=0)

        self.label_canvas = tk.Canvas(canvas_container, width=600, height=300, highlightthickness=1)
        self.label_canvas.grid(row=1, column=1)
        self.label_canvas.bind("<Button-1>", self.on_canvas_click)
        self.label_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.label_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Добавляем контекстное меню
        self.context_menu = tk.Menu(self.label_canvas, tearoff=0)
        self.context_menu.add_command(label="Удалить объект", command=self.delete_selected_object)
        self.label_canvas.bind("<Button-3>", self.show_context_menu)

        self.apply_theme()

        settings_frame = ttk.LabelFrame(content_frame, text="Настройки объекта", padding="15", style='Section.TLabelframe')
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        ttk.Label(settings_frame, text="Поле заказа:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.order_field_menu = ttk.Combobox(settings_frame, textvariable=self.selected_order_field, values=self.order_fields, state="readonly", width=22, font=("Helvetica", 11))
        self.order_field_menu.grid(row=0, column=1, padx=10, pady=10)
        self.order_field_menu.bind("<<ComboboxSelected>>", self.on_order_field_select)

        ttk.Label(settings_frame, text="Текст:", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.text_var = tk.StringVar()
        self.text_entry = ttk.Entry(settings_frame, textvariable=self.text_var, width=25, font=("Helvetica", 12))
        self.text_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text="Размер шрифта:", font=("Helvetica", 12)).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.font_size_var = tk.StringVar(value="12")
        ttk.Entry(settings_frame, textvariable=self.font_size_var, width=10, font=("Helvetica", 12)).grid(row=2, column=1, padx=10, pady=10)

        self.bold_var = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Жирный", variable=self.bold_var).grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.is_custom_var = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Произвольный текст", variable=self.is_custom_var, command=self.toggle_text_entry).grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        ttk.Label(settings_frame, text="Масштаб (для изображений):", font=("Helvetica", 12)).grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.image_scale_var = tk.StringVar(value="1.0")
        ttk.Entry(settings_frame, textvariable=self.image_scale_var, width=10, font=("Helvetica", 12)).grid(row=5, column=1, padx=10, pady=10)

        ttk.Button(settings_frame, text="Применить", command=self.apply_object_settings, style='Accent.TButton').grid(row=6, column=0, columnspan=2, pady=15)

        self.update_label_size()
        self.toggle_text_entry()
        self.draw_rulers()

    def show_context_menu(self, event):
        """Показывает контекстное меню при нажатии правой кнопкой мыши."""
        self.on_canvas_click(event)  # Проверяем, есть ли объект под курсором
        if self.selected_object is not None:
            self.context_menu.entryconfig("Удалить объект", state="normal")
        else:
            self.context_menu.entryconfig("Удалить объект", state="disabled")
        self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_object(self):
        """Удаляет выделенный объект с макета."""
        if self.selected_object is not None:
            del self.label_objects[self.selected_object]
            self.selected_object = None
            self.redraw_label()

    def increase_scale(self):
        self.scale = min(self.scale + 1.0, 10.0)
        self.scale_var.set(f"{self.scale:.1f}")
        self.update_label_size()
        self.draw_rulers()

    def decrease_scale(self):
        self.scale = max(self.scale - 1.0, 1.0)
        self.scale_var.set(f"{self.scale:.1f}")
        self.update_label_size()
        self.draw_rulers()

    def draw_rulers(self):
        self.h_ruler.delete("all")
        self.v_ruler.delete("all")

        try:
            width_mm = float(self.width_var.get())
            height_mm = float(self.height_var.get())
        except ValueError:
            width_mm = 100
            height_mm = 50

        canvas_width = width_mm * self.scale
        canvas_height = height_mm * self.scale

        self.label_canvas.config(width=canvas_width, height=canvas_height)
        self.h_ruler.config(width=canvas_width)
        self.v_ruler.config(height=canvas_height)

        for i in range(0, int(width_mm) + 1, 10):
            x = i * self.scale
            self.h_ruler.create_line(x, 0, x, 30, fill="black")
            self.h_ruler.create_text(x, 15, text=str(i), anchor="center", font=("Helvetica", 8))

        for i in range(0, int(height_mm) + 1, 10):
            y = i * self.scale
            self.v_ruler.create_line(0, y, 30, y, fill="black")
            self.v_ruler.create_text(15, y, text=str(i), anchor="center", font=("Helvetica", 8))

    def toggle_text_entry(self):
        if self.is_custom_var.get():
            self.text_entry.config(state="normal")
            self.order_field_menu.config(state="disabled")
        else:
            self.text_entry.config(state="disabled")
            self.order_field_menu.config(state="readonly")
            self.text_var.set(self.selected_order_field.get())

    def on_order_field_select(self, event):
        if not self.is_custom_var.get():
            self.text_var.set(self.selected_order_field.get())

    def process_queue(self):
        try:
            while True:
                task, data = self.queue.get_nowait()
                if task == "load_orders":
                    self.update_orders(data)
                elif task == "status":
                    self.status_var.set(data)
                elif task == "error":
                    messagebox.showerror("Ошибка", data)
                elif task == "message":
                    messagebox.showinfo("Информация", data)
        except queue.Empty:
            pass
        self.frame.after(100, self.process_queue)

    def update_orders(self, orders):
        pass

    def load_editor_orders(self):
        self.status_var.set("Загрузка заказов...")
        threading.Thread(target=self.load_editor_orders_async, daemon=True).start()

    def load_editor_orders_async(self):
        try:
            orders = self.db.load_orders()
            self.orders_cache = orders
            self.queue.put(("load_orders", orders))
            self.queue.put(("status", "Готов"))
        except Exception as e:
            self.queue.put(("error", f"Не удалось загрузить заказы: {str(e)}"))
            self.queue.put(("status", "Ошибка"))

    def update_label_size(self):
        try:
            width = float(self.width_var.get())
            height = float(self.height_var.get())
            self.label_canvas.config(width=width * self.scale, height=height * self.scale)
            self.draw_rulers()
            self.redraw_label()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные значения для ширины и высоты!")

    def add_text(self):
        obj = {
            "type": "text",
            "text": self.selected_order_field.get() if not self.is_custom_var.get() else self.text_var.get(),
            "x": 10,
            "y": 10,
            "font_size": 12,
            "bold": False,
            "is_custom": self.is_custom_var.get()
        }
        self.label_objects.append(obj)
        self.redraw_label()

    def add_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not file_path:
            return
        obj = {
            "type": "image",
            "path": file_path,
            "x": 10,
            "y": 10,
            "scale": 1.0
        }
        self.label_objects.append(obj)
        self.redraw_label()

    def redraw_label(self):
        self.label_canvas.delete("all")
        for obj in self.label_objects:
            x, y = obj["x"] * self.scale, obj["y"] * self.scale
            if obj["type"] == "text":
                self.label_canvas.create_text(x, y, text=obj["text"], anchor="nw", font=("Helvetica", int(obj["font_size"] * self.scale), "bold" if obj["bold"] else "normal"))
            else:
                img = PILImage.open(obj["path"])
                scale = obj.get("scale", 1.0)
                max_size = int(100 * scale * self.scale)
                img = img.resize((max_size, max_size), PILImage.Resampling.LANCZOS)
                obj["photo"] = ImageTk.PhotoImage(img)
                self.label_canvas.create_image(x, y, image=obj["photo"], anchor="nw")
        self.highlight_selected()

    def on_canvas_click(self, event):
        self.selected_object = None
        for i, obj in enumerate(self.label_objects):
            x, y = obj["x"] * self.scale, obj["y"] * self.scale
            if obj["type"] == "text":
                text_width = len(obj["text"]) * obj["font_size"] * self.scale / 2
                text_height = obj["font_size"] * self.scale
                if x <= event.x <= x + text_width and y <= event.y <= y + text_height:
                    self.selected_object = i
                    break
            else:
                scale = obj.get("scale", 1.0)
                max_size = int(100 * scale * self.scale)
                if x <= event.x <= x + max_size and y <= event.y <= y + max_size:
                    self.selected_object = i
                    break
        self.start_x = event.x
        self.start_y = event.y
        self.highlight_selected()
        if self.selected_object is not None:
            self.load_object_settings()

    def on_canvas_drag(self, event):
        if self.selected_object is not None:
            dx = (event.x - self.start_x) / self.scale
            dy = (event.y - self.start_y) / self.scale
            self.label_objects[self.selected_object]["x"] += dx
            self.label_objects[self.selected_object]["y"] += dy
            self.start_x = event.x
            self.start_y = event.y
            self.redraw_label()

    def on_canvas_release(self, event):
        self.start_x = None
        self.start_y = None

    def highlight_selected(self):
        self.label_canvas.delete("highlight")
        if self.selected_object is not None:
            obj = self.label_objects[self.selected_object]
            x, y = obj["x"] * self.scale, obj["y"] * self.scale
            if obj["type"] == "text":
                text_width = len(obj["text"]) * obj["font_size"] * self.scale / 2
                text_height = obj["font_size"] * self.scale
                self.label_canvas.create_rectangle(x - 2, y - 2, x + text_width + 2, y + text_height + 2, outline="red", tags="highlight")
            else:
                scale = obj.get("scale", 1.0)
                max_size = int(100 * scale * self.scale)
                self.label_canvas.create_rectangle(x - 2, y - 2, x + max_size + 2, y + max_size + 2, outline="red", tags="highlight")

    def load_object_settings(self):
        if self.selected_object is None:
            return
        obj = self.label_objects[self.selected_object]
        self.text_var.set(obj.get("text", ""))
        self.font_size_var.set(str(obj.get("font_size", 12)))
        self.bold_var.set(obj.get("bold", False))
        self.is_custom_var.set(obj.get("is_custom", False))
        self.image_scale_var.set(str(obj.get("scale", 1.0)))
        if obj.get("is_custom", False):
            self.text_entry.config(state="normal")
            self.order_field_menu.config(state="disabled")
        else:
            self.text_entry.config(state="disabled")
            self.order_field_menu.config(state="readonly")
            if obj.get("text") in self.order_fields:
                self.selected_order_field.set(obj.get("text"))

    def apply_object_settings(self):
        if self.selected_object is None:
            return
        obj = self.label_objects[self.selected_object]
        if obj["type"] == "text":
            obj["text"] = self.text_var.get() if self.is_custom_var.get() else self.selected_order_field.get()
            try:
                obj["font_size"] = float(self.font_size_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное значение для размера шрифта!")
                return
            obj["bold"] = self.bold_var.get()
            obj["is_custom"] = self.is_custom_var.get()
        else:
            try:
                obj["scale"] = float(self.image_scale_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное значение для масштаба!")
                return
        self.redraw_label()

    def save_template(self):
        try:
            width = float(self.width_var.get())
            height = float(self.height_var.get())
            template = {
                "width": width,
                "height": height,
                "objects": self.label_objects
            }
            self.label_template.save_template(template)
            messagebox.showinfo("Успех", "Шаблон сохранен!")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные значения для ширины и высоты!")

    def clear_template(self):
        self.label_objects = []
        self.selected_object = None
        self.redraw_label()