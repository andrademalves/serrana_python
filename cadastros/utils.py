"""
Utilitários para validação de documentos
"""

def validar_cpf(cpf):
    """
    Valida um CPF
    """
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 > 9:
        digito1 = 0
    
    # Verifica primeiro dígito
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 > 9:
        digito2 = 0
    
    # Verifica segundo dígito
    if int(cpf[10]) != digito2:
        return False
    
    return True


def validar_cnpj(cnpj):
    """
    Valida um CNPJ
    """
    # Remove caracteres não numéricos
    cnpj = ''.join(filter(str.isdigit, cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcula primeiro dígito verificador
    multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores1[i] for i in range(12))
    digito1 = 11 - (soma % 11)
    if digito1 > 9:
        digito1 = 0
    
    # Verifica primeiro dígito
    if int(cnpj[12]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    multiplicadores2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores2[i] for i in range(13))
    digito2 = 11 - (soma % 11)
    if digito2 > 9:
        digito2 = 0
    
    # Verifica segundo dígito
    if int(cnpj[13]) != digito2:
        return False
    
    return True


def formatar_cpf(cpf):
    """
    Formata CPF no padrão 000.000.000-00
    """
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def formatar_cnpj(cnpj):
    """
    Formata CNPJ no padrão 00.000.000/0000-00
    """
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj
