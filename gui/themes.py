class ThemeManager:
    def __init__(self, style):
        self.style = style
        self.themes = {
            "light": {
                "TFrame": {"background": "#fafafa"},
                "TLabel": {"background": "#fafafa", "foreground": "#2d3748", "font": ("Helvetica", 12)},
                "TLabelFrame": {"background": "#fafafa", "foreground": "#2d3748", "relief": "flat"},
                "TButton": {"background": "#48bb78", "foreground": "#ffffff", "font": ("Helvetica", 11, "bold"), "borderwidth": 0, "padding": 10},
                "TButton_map": {"background": [("active", "#38a169")]},
                "TEntry": {"fieldbackground": "#ffffff", "foreground": "#2d3748", "insertcolor": "#2d3748", "borderwidth": 1, "padding": 8},
                "TCombobox": {"fieldbackground": "#ffffff", "foreground": "#2d3748", "borderwidth": 1, "background": "#ffffff"},
                "TCombobox_map": {"fieldbackground": [("readonly", "#ffffff")], "background": [("readonly", "#ffffff")]},
                "TCheckbutton": {"background": "#fafafa", "foreground": "#2d3748", "font": ("Helvetica", 12)},
                "Treeview": {"background": "#ffffff", "foreground": "#2d3748", "fieldbackground": "#ffffff", "rowheight": 35},
                "Treeview.Heading": {"background": "#edf2f7", "foreground": "#2d3748", "font": ("Helvetica", 12, "bold")},
                "Treeview_map": {"background": [("selected", "#48bb78")]},
                "Scan.TLabelframe": {"background": "#fafafa", "foreground": "#2d3748", "font": ("Helvetica", 16, "bold")},
                "Section.TLabelframe": {"background": "#fafafa", "foreground": "#2d3748", "font": ("Helvetica", 14, "bold")},
                "Large.TButton": {"font": ("Helvetica", 14, "bold"), "padding": 12, "background": "#48bb78", "foreground": "#ffffff"},
                "Large.TButton_map": {"background": [("active", "#38a169")]},
                "Accent.TButton": {"background": "#ed8936", "foreground": "#ffffff", "font": ("Helvetica", 11, "bold"), "padding": 10},
                "Accent.TButton_map": {"background": [("active", "#dd6b20")]},
                "tags": {
                    "closed": {"background": "#48bb78"},  # Зелёный для закрытых коробов
                    "deferred": {"background": "#f6e05e"},  # Жёлтый для отложенных коробов
                    "scanned": {"background": "#48bb78"}  # Зелёный для отсканированных товаров
                }
            },
            "dark": {
                "TFrame": {"background": "#1a202c"},
                "TLabel": {"background": "#1a202c", "foreground": "#e2e8f0", "font": ("Helvetica", 12)},
                "TLabelFrame": {"background": "#1a202c", "foreground": "#e2e8f0", "relief": "flat"},
                "TButton": {"background": "#68d391", "foreground": "#1a202c", "font": ("Helvetica", 11, "bold"), "borderwidth": 0, "padding": 10},
                "TButton_map": {"background": [("active", "#4fbd73")]},
                "TEntry": {"fieldbackground": "#2d3748", "foreground": "#e2e8f0", "insertcolor": "#e2e8f0", "borderwidth": 1, "padding": 8},
                "TCombobox": {"fieldbackground": "#2d3748", "foreground": "#e2e8f0", "borderwidth": 1, "background": "#2d3748"},
                "TCombobox_map": {"fieldbackground": [("readonly", "#2d3748")], "background": [("readonly", "#2d3748")]},
                "TCheckbutton": {"background": "#1a202c", "foreground": "#e2e8f0", "font": ("Helvetica", 12)},
                "Treeview": {"background": "#2d3748", "foreground": "#e2e8f0", "fieldbackground": "#2d3748", "rowheight": 35},
                "Treeview.Heading": {"background": "#4a5568", "foreground": "#e2e8f0", "font": ("Helvetica", 12, "bold")},
                "Treeview_map": {"background": [("selected", "#68d391")]},
                "Scan.TLabelframe": {"background": "#1a202c", "foreground": "#e2e8f0", "font": ("Helvetica", 16, "bold")},
                "Section.TLabelframe": {"background": "#1a202c", "foreground": "#e2e8f0", "font": ("Helvetica", 14, "bold")},
                "Large.TButton": {"font": ("Helvetica", 14, "bold"), "padding": 12, "background": "#68d391", "foreground": "#1a202c"},
                "Large.TButton_map": {"background": [("active", "#4fbd73")]},
                "Accent.TButton": {"background": "#f6ad55", "foreground": "#1a202c", "font": ("Helvetica", 11, "bold"), "padding": 10},
                "Accent.TButton_map": {"background": [("active", "#ed8936")]},
                "tags": {
                    "closed": {"background": "#68d391"},  # Зелёный для закрытых коробов
                    "deferred": {"background": "#d69e2e"},  # Жёлтый для отложенных коробов
                    "scanned": {"background": "#68d391"}  # Зелёный для отсканированных товаров
                }
            }
        }
        self.current_theme = "light"

    def apply_theme(self, theme_name, treeview=None):
        if theme_name not in self.themes:
            return
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        for style_name, config in theme.items():
            if style_name.endswith("_map"):
                base_style = style_name.replace("_map", "")
                self.style.map(base_style, **config)
            elif style_name == "tags":
                if treeview:
                    for tag, tag_config in config.items():
                        treeview.tag_configure(tag, **tag_config)
            else:
                self.style.configure(style_name, **config)

    def get_current_theme(self):
        return self.current_theme

    def switch_theme(self, treeview=None):
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme, treeview)