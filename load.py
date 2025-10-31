import os
import time

def save_uploaded_file(uploaded_file):
    """
    Guarda el archivo en la carpeta 'archivos'. Si ya existe un archivo con el mismo nombre,
    agrega un sufijo con timestamp para evitar sobreescritura.
    Devuelve la ruta completa del archivo guardado.
    """
    os.makedirs("archivos", exist_ok=True)
    filename = uploaded_file.name
    filepath = os.path.join("archivos", filename)

    # Si ya existe, crear un nombre único
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filename)
        timestamp = int(time.time())
        filename = f"{base}_{timestamp}{ext}"
        filepath = os.path.join("archivos", filename)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def list_uploaded_files():
    os.makedirs("archivos", exist_ok=True)
    return sorted([f for f in os.listdir("archivos") if f.lower().endswith((".pdf", ".docx"))])




