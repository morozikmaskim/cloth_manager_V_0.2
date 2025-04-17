import json
import os
from PIL import Image as PILImage, ImageTk

class LabelTemplate:
    def __init__(self):
        self.template_file = "label_template.json"

    def save_template(self, editor):
        template = {
            "width": editor.label_width.get(),
            "height": editor.label_height.get(),
            "objects": []
        }
        for obj in editor.label_objects:
            coords = editor.label_canvas.coords(obj["id"])
            obj_data = {
                "type": obj["type"],
                "x": coords[0],
                "y": coords[1],
                "font_size": obj.get("font_size", 12),
                "bold": obj.get("bold", False)
            }
            if obj["type"] == "text":
                obj_data["text"] = obj["text"]
                obj_data["is_custom"] = obj.get("is_custom", False)
            else:
                obj_data["path"] = obj["path"]
                obj_data["scale"] = obj.get("scale", 1.0)
            template["objects"].append(obj_data)

        try:
            with open(self.template_file, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"Не удалось сохранить шаблон: {str(e)}")

    def load_template(self, editor):
        if not os.path.exists(self.template_file):
            return
        try:
            with open(self.template_file, "r", encoding="utf-8") as f:
                template = json.load(f)

            editor.label_width.set(template["width"])
            editor.label_height.set(template["height"])
            editor.label_canvas.config(width=template["width"], height=template["height"])

            editor.clear_label()

            for obj_data in template["objects"]:
                if obj_data["type"] == "text":
                    display_text = "Datamatrix Code" if obj_data["text"] == "{datamatrix}" else obj_data["text"]
                    font_size = obj_data.get("font_size", 12)
                    font_name = "Arial" if not obj_data.get("bold", False) else "Arial bold"
                    text_id = editor.label_canvas.create_text(
                        obj_data["x"], obj_data["y"], text=display_text,
                        font=(font_name, font_size), anchor="nw", tags="movable"
                    )
                    editor.label_objects.append({
                        "type": "text",
                        "id": text_id,
                        "text": obj_data["text"],
                        "font_size": font_size,
                        "bold": obj_data.get("bold", False),
                        "is_custom": obj_data.get("is_custom", False)
                    })
                else:
                    image = PILImage.open(obj_data["path"])
                    scale = obj_data.get("scale", 1.0)
                    max_size = int(100 * scale)
                    image.thumbnail((max_size, max_size))
                    photo = ImageTk.PhotoImage(image)
                    image_id = editor.label_canvas.create_image(
                        obj_data["x"], obj_data["y"], image=photo, anchor="nw", tags="movable"
                    )
                    editor.label_images.append(photo)
                    editor.label_objects.append({
                        "type": "image",
                        "id": image_id,
                        "image": photo,
                        "path": obj_data["path"],
                        "scale": scale
                    })
        except Exception as e:
            raise Exception(f"Не удалось загрузить шаблон: {str(e)}")
