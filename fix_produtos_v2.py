import shutil
import os

# Caminho completo
arquivo_original = r'c:\HD_Antigo\01- Projetos Dev\1.5 Serrana\cadastros\templates\cadastros\listar_produtos.html'
arquivo_temp = r'c:\HD_Antigo\01- Projetos Dev\1.5 Serrana\cadastros\templates\cadastros\listar_produtos_temp.html'

print('Lendo arquivo original...')
with open(arquivo_original, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total: {len(lines)} linhas')

# Extrair apenas o template de produtos
new_lines = lines[2130:2251]
print(f'Extraídas: {len(new_lines)} linhas')

# Salvar em arquivo temporário
with open(arquivo_temp, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Removendo original...')
os.remove(arquivo_original)

print('Renomeando temp para original...')
os.rename(arquivo_temp, arquivo_original)

print('✓ Concluído!')
