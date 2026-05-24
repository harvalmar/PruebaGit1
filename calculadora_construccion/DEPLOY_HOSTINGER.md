# Despliegue en Hostinger VPS

## Requisitos
- Plan **VPS** de Hostinger (el hosting compartido NO soporta Python)
- Acceso SSH al servidor

## Pasos

### 1. Conectarse por SSH
```bash
ssh usuario@tu-ip-hostinger
```

### 2. Instalar dependencias del sistema
```bash
sudo apt update && sudo apt install python3-pip python3-venv nginx -y
```

### 3. Subir el proyecto (desde tu PC local)
```bash
scp -r calculadora_construccion/ usuario@tu-ip:/var/www/calculadora/
```

### 4. Crear entorno virtual e instalar paquetes
```bash
cd /var/www/calculadora
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Probar que funciona
```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
# Abre http://tu-ip:5000 en el navegador
```

### 6. Configurar como servicio systemd (arranca automático)
```bash
sudo nano /etc/systemd/system/calculadora.service
```
Contenido:
```
[Unit]
Description=Calculadora Construcción Flask
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/calculadora
ExecStart=/var/www/calculadora/venv/bin/gunicorn --workers 2 --bind unix:calculadora.sock wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable calculadora
sudo systemctl start calculadora
```

### 7. Configurar Nginx como proxy inverso
```bash
sudo nano /etc/nginx/sites-available/calculadora
```
Contenido:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;   # o la IP del VPS

    location / {
        proxy_pass http://unix:/var/www/calculadora/calculadora.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/calculadora /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

## Actualizar precios
Edita `app.py` → diccionario `PRECIOS` con los valores actuales de tu región.
