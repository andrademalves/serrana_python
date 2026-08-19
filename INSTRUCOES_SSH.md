# COMANDOS PARA EXECUTAR NO SSH (root@147.79.83.242)

## 1. Conectar ao servidor
ssh root@147.79.83.242

## 2. Navegar até o diretório do projeto
cd /root/serrana
# OU se estiver em outro local:
# cd /var/www/serrana
# cd /home/serrana

## 3. Editar o modelo (adicionar data_nascimento)
nano cadastros/models.py
# Adicionar após a linha do campo 'sexo':
# data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')

## 4. Editar o template editar_pessoa.html
nano cadastros/templates/cadastros/editar_pessoa.html

# Procurar e substituir:
# Linha com CTPS: remover <span class="text-danger" id="asterisco-ctps" style="display:none;">*</span>
# Remover linha: <div class="invalid-feedback">CTPS é obrigatório para funcionários</div>
# Linha com Data Admissão: remover <span class="text-danger" id="asterisco-admissao" style="display:none;">*</span>
# Remover linha: <div class="invalid-feedback">Data de admissão é obrigatória para funcionários</div>

# No JavaScript, alterar:
# const camposObrigatorios = [
#     { nome: 'ctps', asterisco: 'asterisco-ctps' },
#     { nome: 'data_admissao', asterisco: 'asterisco-admissao' }
# ];
# PARA:
# const camposObrigatorios = [];

# Adicionar campo Data de Nascimento após campo Sexo:
# <div class="col-md-3">
#     <label class="form-label">Data de Nascimento</label>
#     <input type="date" class="form-control" name="data_nascimento" value="{{ pessoa.data_nascimento|date:'Y-m-d'|default:'' }}">
# </div>

## 5. Editar views.py
nano cadastros/views.py

# Adicionar após linha 'sexo=request.POST.get...' (na função criar_pessoa):
# data_nascimento=parse_date(request.POST.get('data_nascimento')),

# Adicionar após linha 'pessoa.sexo = request.POST.get...' (na função editar_pessoa):
# pessoa.data_nascimento = parse_date(request.POST.get('data_nascimento'))

## 6. Criar migration
python3 manage.py makemigrations cadastros

## 7. Aplicar migration
python3 manage.py migrate cadastros

## 8. Reiniciar serviço
systemctl restart gunicorn
# OU
systemctl restart uwsgi

## 9. Verificar status
systemctl status gunicorn
