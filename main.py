import tkinter as tk
from tkinter import ttk
from gui.orders_tab import OrdersTab
from gui.label_editor import LabelEditorTab
from gui.themes import ThemeManager

class ClothManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cloth Manager")
        self.root.geometry("1200x800")

        self.style = ttk.Style()
        self.theme_manager = ThemeManager(self.style)
        self.theme_manager.apply_theme("light")

        self.setup_gui()
        self.setup_styles()

    def setup_styles(self):
        self.style.theme_use('clam')
        self.style.configure('TNotebook', background=self.theme_manager.themes[self.theme_manager.get_current_theme()]["TFrame"]["background"], padding=10)
        self.style.configure('TNotebook.Tab', background=self.theme_manager.themes[self.theme_manager.get_current_theme()]["Treeview"]["background"],
                            foreground=self.theme_manager.themes[self.theme_manager.get_current_theme()]["Treeview"]["foreground"],
                            font=("Helvetica", 12, "bold"), padding=(15, 8))
        self.style.map('TNotebook.Tab', background=[('selected', self.theme_manager.themes[self.theme_manager.get_current_theme()]["Treeview_map"]["background"][0][1])])

    def setup_gui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=15, pady=15)
        ttk.Button(top_frame, text="Переключить тему", command=self.switch_theme, style='Accent.TButton').pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.orders_tab = OrdersTab(self.notebook, self.theme_manager)
        self.notebook.add(self.orders_tab.frame, text="Заказы")

        self.label_editor_tab = LabelEditorTab(self.notebook, self.theme_manager)
        self.notebook.add(self.label_editor_tab.frame, text="Редактор этикеток")

    def switch_theme(self):
        self.theme_manager.switch_theme()
        self.setup_styles()
        self.orders_tab.apply_theme()
        self.label_editor_tab.apply_theme()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClothManagerApp(root)
    root.mainloop()