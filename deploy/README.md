# Deploy — Auditel

## Archivos

| Archivo | Destino |
|---|---|
| `systemd/portfolio-auditel.service` | `/etc/systemd/system/` |
| `nginx/portfolio-auditel.conf` | `/etc/nginx/sites-available/` |
| `env/auditel.env.example` | `/etc/default/portfolio-auditel` (completar) |

## Pasos

```bash
# 1. Variables de entorno
sudo cp deploy/env/auditel.env.example /etc/default/portfolio-auditel
sudo nano /etc/default/portfolio-auditel   # completar SECRET_KEY y USER_CREDENTIALS

# 2. Servicio systemd
sudo cp deploy/systemd/portfolio-auditel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now portfolio-auditel

# 3. Nginx
sudo cp deploy/nginx/portfolio-auditel.conf /etc/nginx/sites-available/portfolio-auditel
sudo ln -s /etc/nginx/sites-available/portfolio-auditel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Verificar

```bash
systemctl status portfolio-auditel
curl http://localhost:5003/api/health
```
