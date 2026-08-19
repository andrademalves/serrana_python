from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def processar_foto_3x4(foto):
    """
    Processa e redimensiona a foto para formato 3x4 (proporção 3:4).
    Mantém boa qualidade e centraliza o recorte.
    
    Args:
        foto: Arquivo de imagem enviado
        
    Returns:
        InMemoryUploadedFile: Imagem processada
    """
    if not foto:
        return None
    
    # Abrir a imagem
    img = Image.open(foto)
    
    # Converter para RGB se necessário (remove alpha channel)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Dimensões do formato 3x4 (300x400 pixels é um bom tamanho)
    largura_alvo = 300
    altura_alvo = 400
    proporcao_alvo = largura_alvo / altura_alvo  # 0.75 (3:4)
    
    # Calcular proporção atual
    largura_original, altura_original = img.size
    proporcao_original = largura_original / altura_original
    
    # Redimensionar mantendo a proporção para cobrir o tamanho alvo
    if proporcao_original > proporcao_alvo:
        # Imagem mais larga - ajustar pela altura
        nova_altura = altura_alvo
        nova_largura = int(altura_alvo * proporcao_original)
    else:
        # Imagem mais alta - ajustar pela largura
        nova_largura = largura_alvo
        nova_altura = int(largura_alvo / proporcao_original)
    
    # Redimensionar com alta qualidade
    img = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
    
    # Calcular o crop centralizado
    left = (nova_largura - largura_alvo) // 2
    top = (nova_altura - altura_alvo) // 2
    right = left + largura_alvo
    bottom = top + altura_alvo
    
    # Fazer o crop centralizado
    img = img.crop((left, top, right, bottom))
    
    # Salvar em memória
    output = BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    output.seek(0)
    
    # Retornar como InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        foto.name,
        'image/jpeg',
        sys.getsizeof(output),
        None
    )
