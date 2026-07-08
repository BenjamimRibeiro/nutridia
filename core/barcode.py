"""Leitura de códigos de barras a partir de fotos (câmara/upload) — via zxing-cpp.

Se a biblioteca não estiver instalada, DISPONIVEL fica False e a app continua a
funcionar com a escrita manual do código (fallback gracioso, sem crash).
"""
try:
    import zxingcpp
    from PIL import Image
    DISPONIVEL = True
except ImportError:  # pragma: no cover - depende do ambiente
    DISPONIVEL = False


def ler(ficheiro) -> str | None:
    """Lê o código de barras de uma imagem (UploadedFile/bytes). None se não ler."""
    if not DISPONIVEL:
        return None
    try:
        img = Image.open(ficheiro).convert("RGB")
        res = zxingcpp.read_barcode(img)
        return res.text if res and res.text else None
    except Exception:
        return None
