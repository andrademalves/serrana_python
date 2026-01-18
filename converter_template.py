import re

# Ler o arquivo de criação
with open('cadastros/templates/cadastros/criar_pessoa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir título
content = content.replace('Nova Pessoa', 'Editar Pessoa')
content = content.replace('bi-plus-circle', 'bi-pencil')

# Adicionar valores nos select de Tipo (no topo do form, ajustar display inicial baseado em pessoa.tipo)
content = re.sub(
    r'<div class="col-md-5" id="divNomeFantasia">',
    r'<div class="col-md-5" id="divNomeFantasia" {% if pessoa.tipo == \'F\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divCpf">',
    r'<div class="col-md-3" id="divCpf" {% if pessoa.tipo == \'J\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divCnpj" style="display:none;">',
    r'<div class="col-md-3" id="divCnpj" {% if pessoa.tipo == \'F\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divRg">',
    r'<div class="col-md-3" id="divRg" {% if pessoa.tipo == \'J\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divIe" style="display:none;">',
    r'<div class="col-md-3" id="divIe" {% if pessoa.tipo == \'F\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divDataEmissaoRg">',
    r'<div class="col-md-3" id="divDataEmissaoRg" {% if pessoa.tipo == \'J\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="col-md-3" id="divOrgaoEmissor">',
    r'<div class="col-md-3" id="divOrgaoEmissor" {% if pessoa.tipo == \'J\' %}style="display:none;"{% endif %}>',
    content
)

content = re.sub(
    r'<div class="row mb-3" id="divSexo">',
    r'<div class="row mb-3" id="divSexo" {% if pessoa.tipo == \'J\' %}style="display:none;"{% endif %}>',
    content
)

# Ajustar cliente/fornecedor div
content = re.sub(
    r'<div id="divClienteFornecedor" style="display:none;">',
    r'<div id="divClienteFornecedor" {% if not pessoa.cliente and not pessoa.fornecedor %}style="display:none;"{% endif %}>',
    content
)

# Ajustar funcionário div
content = re.sub(
    r'<div id="divFuncionario" style="display:none;">',
    r'<div id="divFuncionario" {% if not pessoa.funcionario %}style="display:none;"{% endif %}>',
    content
)

# Adicionar valores nos selects
content = re.sub(
    r'(<option value="F")>',
    r'\1 {% if pessoa.tipo == \'F\' %}selected{% endif %}>',
    content
)
content = re.sub(
    r'(<option value="J")>',
    r'\1 {% if pessoa.tipo == \'J\' %}selected{% endif %}>',
    content
)

# Sexo
content = re.sub(
    r'(<option value="M">)(Masculino)',
    r'\1{% if pessoa.sexo == \'M\' %}selected{% endif %}>\2',
    content
)
content = re.sub(
    r'(<option value="F">)(Feminino)',
    r'\1{% if pessoa.sexo == \'F\' %}selected{% endif %}>\2',
    content
)
content = re.sub(
    r'(<option value="O">)(Outro)',
    r'\1{% if pessoa.sexo == \'O\' %}selected{% endif %}>\2',
    content
)

# Escolaridade
escolaridades = [
    'fundamental_incompleto', 'fundamental_completo', 'medio_incompleto', 'medio_completo',
    'superior_incompleto', 'superior_completo', 'pos_graduacao', 'mestrado', 'doutorado'
]
for esc in escolaridades:
    content = re.sub(
        r'(<option value="' + esc + '">)',
        r'\1{% if pessoa.escolaridade == \'' + esc + '\' %}selected{% endif %}>',
        content,
        count=1
    )

# Categoria CNH
categorias_cnh = ['A', 'B', 'AB', 'C', 'D', 'E']
for cat in categorias_cnh:
    content = re.sub(
        r'(<option value="' + cat + '">)' + cat,
        r'\1{% if pessoa.cnh_categoria == \'' + cat + '\' %}selected{% endif %}>' + cat,
        content,
        count=1
    )

# Ajustar label de Nome baseado no tipo
content = re.sub(
    r'<span id="labelNome">Nome</span>',
    r'<span id="labelNome">{% if pessoa.tipo == \'J\' %}Razão Social{% else %}Nome{% endif %}</span>',
    content
)

# Adicionar valores em todos os campos de texto
campos_texto = [
    ('nome', 'pessoa.nome'),
    ('nome_fantasia', 'pessoa.nome_fantasia'),
    ('cpf_cnpj', 'pessoa.cpf_cnpj'),
    ('rg', 'pessoa.rg'),
    ('ie', 'pessoa.ie'),
    ('orgao_emissor', 'pessoa.orgao_emissor'),
    ('cep', 'pessoa.cep'),
    ('logradouro', 'pessoa.logradouro'),
    ('numero', 'pessoa.numero'),
    ('complemento', 'pessoa.complemento'),
    ('bairro', 'pessoa.bairro'),
    ('cidade', 'pessoa.cidade'),
    ('uf', 'pessoa.uf'),
    ('telefone', 'pessoa.telefone'),
    ('celular1', 'pessoa.celular1'),
    ('celular2', 'pessoa.celular2'),
    ('email', 'pessoa.email'),
    ('ramo_atividade', 'pessoa.ramo_atividade'),
    ('descricao_ramo', 'pessoa.descricao_ramo'),
    ('titulo_eleitoral', 'pessoa.titulo_eleitoral'),
    ('zona', 'pessoa.zona'),
    ('secao', 'pessoa.secao'),
    ('ctps', 'pessoa.ctps'),
    ('serie', 'pessoa.serie'),
    ('uf_ctps', 'pessoa.uf_ctps'),
    ('cnh', 'pessoa.cnh'),
    ('cargo', 'pessoa.cargo'),
]

for campo, valor in campos_texto:
    # Buscar o padrão sem value
    pattern = r'(<input[^>]+name="' + campo + '"[^>]+(?<!value=")(?<!value=\'\'))(>)'
    replacement = r'\1 value="{{ ' + valor + '|default:\'\' }}">\2'
    content = re.sub(pattern, replacement, content)

# Campos de data
campos_data = [
    ('data_emissao_rg', 'pessoa.data_emissao_rg'),
    ('data_expedicao_ctps', 'pessoa.data_expedicao_ctps'),
    ('data_admissao', 'pessoa.data_admissao'),
    ('data_demissao', 'pessoa.data_demissao'),
]

for campo, valor in campos_data:
    pattern = r'(<input[^>]+name="' + campo + '"[^>]+)(>)'
    replacement = r'\1 value="{{ ' + valor + '|date:\'Y-m-d\'|default:\'\' }}">\2'
    content = re.sub(pattern, replacement, content)

# Checkboxes
checkboxes = ['cliente', 'fornecedor', 'terceiro', 'deficiencia']
for checkbox in checkboxes:
    pattern = r'(<input class="form-check-input" type="checkbox" name="' + checkbox + '"[^>]+)(>)'
    replacement = r'\1 {% if pessoa.' + checkbox + ' %}checked{% endif %}>\2'
    content = re.sub(pattern, replacement, content)

# Checkbox funcionário (tem id diferente)
content = re.sub(
    r'(<input class="form-check-input" type="checkbox" name="funcionario"[^>]+)(>)',
    r'\1 {% if pessoa.funcionario %}checked{% endif %}>\2',
    content
)

# Textarea
content = re.sub(
    r'(<textarea class="form-control" name="observacoes"[^>]+>)(</textarea>)',
    r'\1{{ pessoa.observacoes|default:\'\' }}\2',
    content
)

# Salvar o arquivo de edição
with open('cadastros/templates/cadastros/editar_pessoa.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Template de edição criado com sucesso!')
