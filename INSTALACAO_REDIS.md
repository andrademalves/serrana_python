# 🔴 INSTALAÇÃO DO REDIS NO WINDOWS

## Opção 1: Via Chocolatey (Recomendado)

```powershell
# Instalar Chocolatey (se não tiver)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Instalar Redis
choco install redis-64 -y

# Iniciar Redis como serviço
redis-server --service-start

# Testar
redis-cli ping
# Deve retornar: PONG
```

## Opção 2: Download Direto

1. **Baixar Redis para Windows:**
   https://github.com/microsoftarchive/redis/releases

2. **Versão recomendada:** Redis-x64-3.0.504.msi

3. **Instalar e marcar:**
   - ✅ Add to PATH
   - ✅ Install as Windows Service

4. **Iniciar serviço:**
   ```powershell
   net start Redis
   ```

5. **Testar:**
   ```powershell
   redis-cli ping
   ```

## Opção 3: Docker (Mais Moderno)

```powershell
# Instalar Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Executar Redis
docker run -d -p 6379:6379 --name redis-serrana redis:alpine

# Testar
docker exec -it redis-serrana redis-cli ping
```

## Após Instalar Redis

**Atualizar settings.py:**

Comentar a configuração atual de cache em memória e descomentar a configuração Redis:

```python
# serrana/settings.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'serrana',
        'TIMEOUT': 3600,
    }
}
```

## Testar Configuração

```python
# python manage.py shell

from django.core.cache import cache
cache.set('test', 'OK', 60)
print(cache.get('test'))  # Deve retornar: OK
```

## Iniciar Celery (após Redis instalado)

```powershell
# Terminal 1 - Celery Worker
celery -A serrana worker -l info --pool=solo

# Terminal 2 - Celery Beat (agendador)
celery -A serrana beat -l info

# Terminal 3 - Django
python manage.py runserver
```

## Status Atual

🟡 **Sistema funcionando com cache em memória** (LocMemCache)
- Dashboard BI está acessível
- Performance OK para desenvolvimento
- Para produção, instale Redis para melhor performance

🟢 **Após instalar Redis:**
- Cache distribuído
- Melhor performance
- Suporte a Celery tasks assíncronas
