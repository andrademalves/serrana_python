# COMO APLICAR AS ALTERAÇÕES NO SERVIDOR SSH

## O projeto está em: /root/serrana_python

## OPÇÃO 1: Usar o script Python automatizado

### Passo 1: Copiar o script para o servidor
```bash
# No seu computador local:
scp aplicar_alteracoes_servidor.py root@147.79.83.242:/root/
```

### Passo 2: Executar no servidor
```bash
# Conectar ao SSH
ssh root@147.79.83.242

# Executar o script
python3 /root/aplicar_alteracoes_servidor.py
```

---

## OPÇÃO 2: Comandos manuais diretos

Conecte ao SSH e execute os comandos abaixo:

```bash
ssh root@147.79.83.242

cd /root/serrana_python

# 1. Editar models.py - Adicionar data_nascimento
sed -i "/sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name='Sexo')/a\\    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')" cadastros/models.py

# 2. Remover obrigatoriedade CTPS
sed -i 's/<label class="form-label">CTPS <span class="text-danger" id="asterisco-ctps" style="display:none;">\*<\/span><\/label>/<label class="form-label">CTPS<\/label>/g' cadastros/templates/cadastros/editar_pessoa.html
sed -i '/<div class="invalid-feedback">CTPS é obrigatório para funcionários<\/div>/d' cadastros/templates/cadastros/editar_pessoa.html

# 3. Remover obrigatoriedade Data Admissão
sed -i 's/<label class="form-label">Data Admissão <span class="text-danger" id="asterisco-admissao" style="display:none;">\*<\/span><\/label>/<label class="form-label">Data Admissão<\/label>/g' cadastros/templates/cadastros/editar_pessoa.html
sed -i '/<div class="invalid-feedback">Data de admissão é obrigatória para funcionários<\/div>/d' cadastros/templates/cadastros/editar_pessoa.html

# 4. Limpar campos obrigatórios no JavaScript
sed -i "s/const camposObrigatorios = \[.*\];/const camposObrigatorios = [];/g" cadastros/templates/cadastros/editar_pessoa.html

# 5. Criar migration
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

# 6. Atualizar views.py
sed -i "/sexo=request.POST.get('sexo', '') or None,/a\\                data_nascimento=parse_date(request.POST.get('data_nascimento'))," cadastros/views.py
sed -i "/pessoa.sexo = request.POST.get('sexo', '') or None/a\\            pessoa.data_nascimento = parse_date(request.POST.get('data_nascimento'))" cadastros/views.py

# 7. Aplicar migration
python3 manage.py migrate cadastros

# 8. Reiniciar serviço
systemctl restart gunicorn
# OU se usar uwsgi:
# systemctl restart uwsgi

# 9. Verificar status
systemctl status gunicorn
```

---

## RESUMO DAS ALTERAÇÕES

✅ **CTPS**: Removida obrigatoriedade (agora é opcional)
✅ **Data de Admissão**: Removida obrigatoriedade (agora é opcional)  
✅ **Data de Nascimento**: Novo campo adicionado (opcional)

---

## VERIFICAR SE DEU CERTO

Após aplicar, acesse o sistema e vá em:
Cadastros → Pessoas → Editar Pessoa

Você deve ver:
- Campo CTPS sem asterisco vermelho
- Campo Data Admissão sem asterisco vermelho  
- Campo Data de Nascimento ao lado do campo Sexo
