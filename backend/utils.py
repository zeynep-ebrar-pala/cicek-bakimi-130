import base64
import os

def get_image_base64(path):
    """Local imajları HTML içinde göstermek için base64'e çevirir."""
    if not path or path.startswith("http"):
        return path
    
    # Path düzeltme (Mutlak kök dizini üzerinden kontrol et)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = path
    
    if not os.path.exists(full_path):
        # Önce root/assets içinde dene (ana yer)
        test_path = os.path.join(root_dir, "assets", path)
        if os.path.exists(test_path):
            full_path = test_path
        else:
            # Sonra frontend/assets içinde dene (alternatif)
            test_path = os.path.join(root_dir, "frontend", "assets", path)
            if os.path.exists(test_path):
                full_path = test_path
        
    if os.path.exists(full_path):
        try:
            with open(full_path, "rb") as image_file:
                ext = full_path.split('.')[-1].lower()
                mime_type = "jpeg" if ext == "jpg" else ext
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/{mime_type};base64,{encoded_string}"
        except Exception:
            return "https://via.placeholder.com/400x300?text=Resim+Yuklenemedi"
            
    return "https://via.placeholder.com/400x300?text=Resim+Yok"
