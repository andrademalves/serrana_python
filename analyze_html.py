import re

with open('criar_pessoa_current.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find divFuncionario start
start_line = None
for i, line in enumerate(lines, 1):
    if 'id="divFuncionario"' in line:
        start_line = i
        break

print(f'divFuncionario starts at line {start_line}')

# Count div balance from that line
balance = 0
for i, line in enumerate(lines[start_line-1:], start_line):
    opens = len(re.findall(r'<div[\s>]', line))
    closes = len(re.findall(r'</div>', line))
    balance += opens - closes
    if opens or closes:
        print(f'Line {i:3d} [{balance:+d}]: {line.rstrip()}')
    if balance == 0:
        print(f'--- divFuncionario CLOSES at line {i} ---')
        for j in range(i, min(i+8, len(lines))):
            print(f'  After +{j-i+1}: {lines[j].rstrip()}')
        break
