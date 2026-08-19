#!/usr/bin/env python3
"""
Analisa o template criar_pessoa.html e insere o </div> correto
para fechar o divFuncionario antes da secao Observacoes.
"""
filepath = "/root/serrana_python/cadastros/templates/cadastros/criar_pessoa.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Localizar onde o divFuncionario abre
func_start = content.find('<div id="divFuncionario"')
if func_start == -1:
    print("ERRO: divFuncionario nao encontrado")
    exit(1)

# Localizar onde a hr antes de Observacoes comeca
# O byte 0x02 esta na linha que deveria ser o fechamento do divFuncionario
# Vamos localizar esse byte
byte02_pos = content.find('\x02')
print(f"Byte 0x02 encontrado em posicao: {byte02_pos}")

# Localizar onde a secao Observacoes comeca (pelo <hr> seguido de Observacoes)
hr_obs = "\n\n            <hr>\n"
hr_pos = content.find(hr_obs, func_start)
if hr_pos == -1:
    print("ERRO: <hr> antes de Observacoes nao encontrado")
    exit(1)

# Contar divs entre o inicio do divFuncionario e o <hr>
section = content[func_start:hr_pos]
opens = section.count('<div')
closes = section.count('</div')
# subtract the \x02 since it represents the missing </div>
byte02_in_section = section.count('\x02')
balance = opens - closes + byte02_in_section  # byte02 conta como div aberto sem fechar

print(f"Divs abertos no divFuncionario: {opens}")
print(f"Divs fechados no divFuncionario: {closes}")
print(f"Bytes 0x02 na secao: {byte02_in_section}")
print(f"Balanco real (faltam fechar): {balance}")

# Substituir o byte 0x02 + inserir os demais fechamentos necessarios
divs_to_insert = '\n'.join(['            </div>'] * balance)

# Substituir o byte 0x02 pelos fechamentos necessarios
if byte02_in_section > 0:
    new_content = content.replace('\x02', divs_to_insert, 1)
else:
    # Inserir antes do <hr>
    new_content = content[:hr_pos] + '\n' + divs_to_insert + content[hr_pos:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"\nInseridos {balance} fechamento(s) </div>")
print("Arquivo salvo com sucesso!")

# Verificacao final
with open(filepath, "r", encoding="utf-8") as f:
    final = f.read()
func_start2 = final.find('<div id="divFuncionario"')
hr_pos2 = final.find(hr_obs, func_start2)
section2 = final[func_start2:hr_pos2]
o2 = section2.count('<div')
c2 = section2.count('</div')
print(f"\nVerificacao: opens={o2} closes={c2} balance={o2-c2} (deve ser 0)")
