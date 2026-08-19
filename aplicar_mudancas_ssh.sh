#!/bin/bash
# Script para aplicar mudanças no servidor SSH

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Aplicando mudanças no cadastro de pessoas ===${NC}"

# Localizar o diretório do projeto
cd /root/serrana || cd /var/www/serrana || cd /home/serrana || cd ~/serrana || { echo "Diretório do projeto não encontrado!"; exit 1; }

echo -e "${GREEN}Diretório do projeto: $(pwd)${NC}"

# 1. Adicionar campo data_nascimento no modelo
echo -e "${BLUE}1. Adicionando campo data_nascimento no modelo...${NC}"
sed -i "/sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name='Sexo')/a\\    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')" cadastros/models.py

# 2. Criar migration
echo -e "${BLUE}2. Criando arquivo de migration...${NC}"
cat > cadastros/migrations/0008_pessoa_data_nascimento.py << 'EOF'
# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0007_rename_pessoa_emp_ativo_idx_cadastros_p_empresa_b3572f_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pessoa',
            name='data_nascimento',
            field=models.DateField(blank=True, null=True, verbose_name='Data de Nascimento'),
        ),
    ]
EOF

# 3. Atualizar template editar_pessoa.html - Remover obrigatoriedade CTPS e Data Admissão
echo -e "${BLUE}3. Removendo obrigatoriedade de CTPS e Data Admissão...${NC}"

# Remover asterisco e mensagem de erro do CTPS
sed -i 's/<label class="form-label">CTPS <span class="text-danger" id="asterisco-ctps" style="display:none;">\*<\/span><\/label>/<label class="form-label">CTPS<\/label>/g' cadastros/templates/cadastros/editar_pessoa.html
sed -i '/<div class="invalid-feedback">CTPS é obrigatório para funcionários<\/div>/d' cadastros/templates/cadastros/editar_pessoa.html

# Remover asterisco e mensagem de erro da Data Admissão
sed -i 's/<label class="form-label">Data Admissão <span class="text-danger" id="asterisco-admissao" style="display:none;">\*<\/span><\/label>/<label class="form-label">Data Admissão<\/label>/g' cadastros/templates/cadastros/editar_pessoa.html
sed -i '/<div class="invalid-feedback">Data de admissão é obrigatória para funcionários<\/div>/d' cadastros/templates/cadastros/editar_pessoa.html

# Limpar array de campos obrigatórios
sed -i 's/const camposObrigatorios = \[.*\];/const camposObrigatorios = [];/g' cadastros/templates/cadastros/editar_pessoa.html

# 4. Adicionar campo data_nascimento nos templates
echo -e "${BLUE}4. Adicionando campo Data de Nascimento nos templates...${NC}"

# Adicionar no editar_pessoa.html (após campo Sexo)
sed -i '/<\/select>/a\                </div>\n                <div class="col-md-3">\n                    <label class="form-label">Data de Nascimento</label>\n                    <input type="date" class="form-control" name="data_nascimento" value="{{ pessoa.data_nascimento|date:'\''Y-m-d'\''|default:'\'''\'' }}">' cadastros/templates/cadastros/editar_pessoa.html

# 5. Atualizar views.py para incluir data_nascimento
echo -e "${BLUE}5. Atualizando views.py...${NC}"
sed -i "/sexo=request.POST.get('sexo', '') or None,/a\\                data_nascimento=parse_date(request.POST.get('data_nascimento'))," cadastros/views.py
sed -i "/pessoa.sexo = request.POST.get('sexo', '') or None/a\\            pessoa.data_nascimento = parse_date(request.POST.get('data_nascimento'))" cadastros/views.py

# 6. Aplicar migration
echo -e "${BLUE}6. Aplicando migration...${NC}"
python3 manage.py migrate cadastros

# 7. Reiniciar serviço (ajuste conforme necessário)
echo -e "${BLUE}7. Reiniciando serviço...${NC}"
if systemctl is-active --quiet gunicorn; then
    systemctl restart gunicorn
    echo -e "${GREEN}Gunicorn reiniciado${NC}"
elif systemctl is-active --quiet uwsgi; then
    systemctl restart uwsgi
    echo -e "${GREEN}uWSGI reiniciado${NC}"
else
    echo -e "${GREEN}Nenhum serviço encontrado para reiniciar${NC}"
fi

echo -e "${GREEN}=== Mudanças aplicadas com sucesso! ===${NC}"
