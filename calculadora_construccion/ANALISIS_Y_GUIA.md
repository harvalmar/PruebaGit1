# Calculadora de Costos LSF y Construcción en Seco
## Análisis completo, diagrama de flujo y guía de uso

---

## TABLA DE CONTENIDO

1. [Análisis del código](#1-análisis-del-código)
2. [Diagrama de flujo](#2-diagrama-de-flujo-del-código)
3. [Descarga e instalación paso a paso](#3-descarga-e-instalación-paso-a-paso)
4. [Ejecución en Visual Studio Code](#4-ejecución-en-visual-studio-code)
5. [¿Qué es GitHub y para qué sirve aquí?](#5-qué-es-github-y-para-qué-sirve-aquí)
6. [Publicación en Hostinger](#6-publicación-en-hostinger)
7. [Alternativas a Hostinger](#7-alternativas-más-fáciles-que-hostinger)

---

# 1. Análisis del código

## 1.1 Estructura del proyecto

```
calculadora_construccion/
│
├── app.py                       ← Cerebro de la aplicación (Python/Flask)
├── wsgi.py                      ← Punto de entrada para servidor de producción
├── requirements.txt             ← Lista de paquetes Python necesarios
│
├── templates/                   ← Páginas HTML que ve el usuario
│   ├── index.html               ← Formulario de entrada
│   └── resultado.html           ← Pantalla con el presupuesto
│
├── static/
│   └── css/
│       └── style.css            ← Estilos visuales (colores, espacios)
│
├── DEPLOY_HOSTINGER.md          ← Guía técnica de despliegue
└── ANALISIS_Y_GUIA.md           ← Este documento
```

**Tamaño total:** 922 líneas de código repartidas en 4 archivos editables.

---

## 1.2 Arquitectura — Patrón MVC

La app sigue el patrón **Modelo-Vista-Controlador**:

| Capa | Archivo | Responsabilidad |
|---|---|---|
| **Modelo** (datos + cálculos) | `app.py` → diccionario `PRECIOS` y funciones `calcular_*` | Guarda los precios y aplica la matemática |
| **Vista** (lo que ves) | `templates/*.html` + `static/css/style.css` | Renderiza el formulario y los resultados |
| **Controlador** (lógica web) | `app.py` → rutas `@app.route(...)` | Recibe lo que envía el navegador y decide qué hacer |

---

## 1.3 Análisis archivo por archivo

### 📄 `app.py` — 319 líneas

Es el corazón del programa. Se divide en 5 bloques:

#### Bloque 1: Diccionario `PRECIOS` (líneas ~10–70)
```python
PRECIOS = {
    "construccion_seca": { ... },   # Precios para drywall interior
    "lsf_muros":         { ... },   # Precios del sistema de muros LSF
    "lsf_techo":         { ... },   # Precios del sistema de techo
}
```
Cada precio está en **USD por m²** y es **editable** sin tocar el resto del código.

#### Bloque 2: Constantes financieras
```python
INDIRECTOS_PCT = 0.20    # 20% gastos generales y utilidad
IVA_PCT        = 0.19    # 19% IVA Colombia
```

#### Bloque 3: Funciones de cálculo (las "fórmulas")
| Función | Qué hace |
|---|---|
| `factor_pendiente(pct)` | Convierte pendiente del techo en factor de área real |
| `calcular_construccion_seca(...)` | Suma ítems del sistema drywall |
| `calcular_lsf_muros(...)` | Suma todos los ítems del muro LSF (15+ items) |
| `calcular_lsf_techo(...)` | Suma ítems del techo según tipo (plano/un agua/dos aguas) |
| `resumen_financiero(...)` | Aplica indirectos + IVA → da el total |

#### Bloque 4: Rutas Flask (qué responde cuando el navegador llama)
| URL | Método | Qué hace |
|---|---|---|
| `/` | GET | Devuelve el formulario `index.html` |
| `/calcular` | POST | Recibe el formulario y devuelve `resultado.html` |
| `/api/calcular` | POST | Devuelve los cálculos en formato JSON (para integraciones) |

#### Bloque 5: Arranque del servidor
```python
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

---

### 📄 `templates/index.html` — 334 líneas

Es la pantalla principal con el formulario. Tres bloques clave:

1. **Selector de técnica** (Construcción en Seco vs LSF) — cambia las opciones visibles con JavaScript.
2. **Datos generales** — área, pisos (máximo 2, limitación legal Colombia).
3. **Opciones específicas** — acabados, EPS, tipo de techo, pendiente.

Usa **Bootstrap 5** vía CDN (no hay que descargar nada extra) y un poco de JavaScript inline para:
- Mostrar/ocultar secciones según la técnica elegida
- Calcular en vivo el ángulo y factor de área cuando se cambia la pendiente

---

### 📄 `templates/resultado.html` — 229 líneas

Muestra el presupuesto en **2 tablas separadas** (muros y techo) más un **resumen financiero** con:
- Subtotal por sección
- Costos directos totales
- Indirectos (20%)
- IVA (19%)
- TOTAL
- Costo por m²
- Botón de imprimir/PDF

---

### 📄 `static/css/style.css` — 40 líneas

Personalización visual mínima sobre Bootstrap: sombras suaves, bordes redondeados, estilo de las tarjetas de opción y reglas `@media print` para imprimir sin la barra de navegación.

---

### 📄 `wsgi.py` — 4 líneas

Punto de entrada para servidores de producción (gunicorn, uWSGI). En local **no se usa**.

---

### 📄 `requirements.txt` — 2 líneas

```
flask>=3.0.0
gunicorn>=21.0.0
```
Lista las librerías Python que `pip install` debe instalar.

---

## 1.4 Modelo matemático

Para cada ítem `i`:
```
Costo_i = precio_unitario_i × área × número_pisos
```

Para techos inclinados:
```
área_real = área_planta × 1 / cos( arctan(pendiente% / 100) )
```

Resumen financiero:
```
CD     = Σ (todos los costos directos)
CI     = CD × 0.20         (indirectos)
ST     = CD + CI           (subtotal sin IVA)
IVA    = ST × 0.19
TOTAL  = ST + IVA          ≈ CD × 1.428
```

Por cada **$1 de costo directo**, el cliente paga **$1.43 final**.

---

# 2. Diagrama de flujo del código

```
┌─────────────────────────────────────────────────────────────────┐
│  USUARIO abre el navegador en  http://localhost:5000            │
└────────────────────────┬────────────────────────────────────────┘
                         │  GET /
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flask ejecuta  app.index()                                     │
│  → renderiza  templates/index.html                              │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTML llega al navegador
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  USUARIO ve el formulario, llena los campos y presiona          │
│  "Calcular presupuesto"                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │  POST /calcular  (con todos los datos)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flask ejecuta  app.calcular()                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Extrae datos del formulario (técnica, área, pisos…)    │  │
│  │ 2. Valida que área > 0 y pisos entre 1 y 2                │  │
│  └─────────────────┬─────────────────────────────────────────┘  │
│                    ▼                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ¿Qué técnica eligió?                         │  │
│  └──┬──────────────────────────────────────────────┬─────────┘  │
│     │ "seca"                                       │ "lsf"      │
│     ▼                                              ▼            │
│  ┌──────────────────────┐    ┌─────────────────────────────┐    │
│  │ calcular_            │    │ calcular_lsf_muros(...)     │    │
│  │   construccion_seca()│    │  → dict con ~15 ítems       │    │
│  │ → dict con 6 ítems   │    └──────────────┬──────────────┘    │
│  └──────────┬───────────┘                   │                   │
│             │                               ▼                   │
│             │                ┌─────────────────────────────┐    │
│             │                │ calcular_lsf_techo(...)     │    │
│             │                │  · Si plano   → área = base │    │
│             │                │  · Si inclin. → aplica      │    │
│             │                │    factor 1/cos(arctan…)    │    │
│             │                │ → dict con 4–8 ítems        │    │
│             │                └──────────────┬──────────────┘    │
│             │                               │                   │
│             └────────────────┬──────────────┘                   │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ resumen_financiero(detalle_muros, detalle_techo)          │  │
│  │  · Suma todos los costos directos                         │  │
│  │  · Aplica 20% de indirectos                               │  │
│  │  · Aplica 19% de IVA                                      │  │
│  │  · Devuelve diccionario con todos los subtotales          │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
│                                ▼                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Renderiza  templates/resultado.html  con todos los datos  │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │  HTML del resultado
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  USUARIO ve el presupuesto:                                     │
│  · Tabla muros (subtotal)                                       │
│  · Tabla techo (subtotal)                                       │
│  · Resumen financiero con IVA                                   │
│  · Costo por m²                                                 │
│  · Botón "Imprimir / PDF"                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

# 3. Descarga e instalación paso a paso

## 3.1 Requisitos previos en tu PC

Antes de descargar, asegúrate de tener instalado:

| Programa | Versión | Para qué | Cómo obtenerlo |
|---|---|---|---|
| **Python** | 3.10 o superior | Ejecutar la app | https://www.python.org/downloads/ |
| **Git** | Cualquiera | Descargar del repositorio | https://git-scm.com/downloads |
| **Visual Studio Code** | Cualquiera | Editar el código | https://code.visualstudio.com/ |

> 💡 Cuando instales **Python en Windows**, marca la casilla **"Add Python to PATH"** durante la instalación. Es crítico.

---

## 3.2 Opción A — Descargar como ZIP (la más fácil)

1. Abre tu navegador y entra a:
   ```
   https://github.com/harvalmar/PruebaGit1
   ```

2. **Cambia a la rama correcta:** haz click en el botón que dice `master` (arriba a la izquierda del listado de archivos) y elige:
   ```
   claude/dry-construction-cost-calc-LDPUu
   ```

3. Haz click en el botón verde **`< > Code`** → **Download ZIP**.

4. Descomprime el ZIP en una carpeta de tu PC, por ejemplo:
   - Windows: `C:\Users\TuUsuario\Documents\PruebaGit1\`
   - Mac/Linux: `/home/tuusuario/Documents/PruebaGit1/`

5. Dentro encontrarás la carpeta `calculadora_construccion/` con todos los archivos.

---

## 3.3 Opción B — Clonar con Git (recomendado si quieres actualizar después)

Abre una terminal (PowerShell en Windows, Terminal en Mac/Linux) y ejecuta:

```bash
git clone https://github.com/harvalmar/PruebaGit1.git
cd PruebaGit1
git checkout claude/dry-construction-cost-calc-LDPUu
```

**Ventaja:** Cuando se actualice el código en GitHub, solo escribes `git pull` y todo se actualiza solo.

---

## 3.4 Estructura que verás después de descargar

```
PruebaGit1/                              ← Carpeta principal del repositorio
├── README.md
├── index.html                           ← Otros archivos del repo (no son de la app)
├── app.js
├── style.css
└── calculadora_construccion/            ← ⭐ La app está aquí
    ├── app.py                           ← Lo que vas a ejecutar
    ├── wsgi.py
    ├── requirements.txt
    ├── DEPLOY_HOSTINGER.md
    ├── ANALISIS_Y_GUIA.md               ← Este documento
    ├── templates/
    │   ├── index.html
    │   └── resultado.html
    └── static/
        └── css/
            └── style.css
```

---

# 4. Ejecución en Visual Studio Code

### Paso 1 — Abrir la carpeta del proyecto
- Abre **VS Code**
- Menú: `Archivo → Abrir carpeta…`
- Selecciona la carpeta **`PruebaGit1`** (la principal)

### Paso 2 — Instalar la extensión de Python
- En la barra lateral izquierda, ícono de extensiones (o `Ctrl+Shift+X`)
- Busca **"Python"** (la oficial de Microsoft)
- Click en **Install**

### Paso 3 — Abrir la terminal integrada
- Menú: `Ver → Terminal` (atajo: `` Ctrl+Ñ `` o `` Ctrl+` ``)
- Se abrirá una terminal abajo

### Paso 4 — Entrar a la carpeta de la app
```bash
cd calculadora_construccion
```

### Paso 5 — Crear un entorno virtual (recomendado)
Un entorno virtual aísla los paquetes Python de la app para no afectar otros proyectos.

```bash
python -m venv venv
```

Luego **activarlo**:

| Sistema | Comando |
|---|---|
| **Windows (PowerShell)** | `venv\Scripts\activate` |
| **Windows (CMD)** | `venv\Scripts\activate.bat` |
| **Mac / Linux** | `source venv/bin/activate` |

Cuando esté activo verás `(venv)` al inicio de la línea.

> ⚠️ **Windows:** Si te da error de "scripts deshabilitados", ejecuta primero esto en PowerShell:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Paso 6 — Instalar las dependencias
```bash
pip install -r requirements.txt
```
Esto instala Flask y Gunicorn.

### Paso 7 — Ejecutar la app
```bash
python app.py
```

Verás algo así:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
Press CTRL+C to quit
```

### Paso 8 — Abrir en el navegador
Abre cualquier navegador y entra a:
```
http://127.0.0.1:5000
```
o equivalente:
```
http://localhost:5000
```

### Paso 9 — Detener la app
En la terminal de VS Code, presiona **`Ctrl + C`**.

---

### Para la próxima vez

Solo necesitas:
```bash
cd calculadora_construccion
venv\Scripts\activate         # Windows
# o: source venv/bin/activate  # Mac/Linux
python app.py
```

---

# 5. ¿Qué es GitHub y para qué sirve aquí?

## 5.1 ¿Qué es GitHub?

GitHub es una **plataforma web para guardar y compartir código**, basada en una tecnología llamada **Git** que registra todos los cambios que se hacen a los archivos. Piensa en GitHub como:

- 🗄️ **Un Google Drive especializado para código** — guarda tus archivos en la nube.
- 🕰️ **Una máquina del tiempo** — guarda cada cambio que haces, puedes volver atrás cuando quieras.
- 👥 **Una plataforma de trabajo en equipo** — varias personas pueden editar el mismo proyecto sin pisarse.

## 5.2 ¿Qué pinta GitHub en nuestro proyecto?

Yo (la IA) edité y subí todo el código a tu repositorio:
```
https://github.com/harvalmar/PruebaGit1
```

Está guardado en una **rama** (branch) llamada:
```
claude/dry-construction-cost-calc-LDPUu
```

Una rama es una **línea de trabajo paralela**. Funciona así:

```
master           ●──────●──────●─────────────────────────●
                              ╲                          ╱
claude/dry-...                 ●──●──●──●──●  ← aquí está la app
                              (5 commits con todo el progreso)
```

La rama `master` es la principal. La rama `claude/dry-...` contiene la calculadora. Esto permite tener varias versiones del proyecto sin mezclarlas.

## 5.3 Conceptos clave que verás

| Término | Significado |
|---|---|
| **Repositorio (repo)** | Carpeta del proyecto en GitHub |
| **Commit** | Una "foto" de los archivos en un momento dado |
| **Branch (rama)** | Línea de trabajo paralela |
| **Pull** | Bajar los cambios de GitHub a tu PC |
| **Push** | Subir tus cambios de tu PC a GitHub |
| **Clone** | Descargar el repo completo por primera vez |
| **Merge** | Fusionar una rama con otra |
| **Pull Request (PR)** | Pedir que se incorporen los cambios de una rama a otra (con revisión) |

## 5.4 Comandos básicos de Git

```bash
# Bajar los últimos cambios de GitHub
git pull

# Ver qué archivos modificaste
git status

# Guardar tus cambios localmente
git add .
git commit -m "Descripción de qué cambiaste"

# Subir tus cambios a GitHub
git push
```

## 5.5 ¿Necesitas GitHub para correr la app?

**No.** Solo necesitas los archivos en tu PC. GitHub es para:
- ✅ Tener un backup en la nube
- ✅ Ver el historial de cambios
- ✅ Compartir con otros
- ✅ Desplegar fácilmente a servidores
- ✅ Recibir actualizaciones si alguien edita el código

---

# 6. Publicación en Hostinger

## 6.1 ¿Qué planes de Hostinger SÍ permiten Python?

| Plan | ¿Soporta Flask? | Por qué |
|---|---|---|
| ❌ **Premium / Business / Cloud Hosting** | NO | Solo soportan PHP/HTML/MySQL (orientado a WordPress) |
| ✅ **VPS Hostinger (KVM 1, 2, 4, 8)** | SÍ | Servidor virtual completo, tienes control total |
| ⚠️ **Cloud Startup / Pro** | A veces | Depende de la configuración, no es directo |

**Lo que necesitas:** un plan **VPS**. El más económico es el KVM 1 (~$5–7 USD/mes).

## 6.2 ¿Cómo saber qué plan tienes?

1. Entra a tu panel de Hostinger: https://hpanel.hostinger.com
2. En el menú lateral verás **"Hosting"** o **"VPS"**.
3. Si dice **"Hosting"** y muestra dominios con cPanel: es **hosting compartido** (no sirve para Flask).
4. Si dice **"VPS"** y muestra opciones como "SSH access", "Browser terminal", "Reinstall OS": es un **VPS** (sirve).

## 6.3 Despliegue en VPS — paso a paso

> 📘 El archivo `DEPLOY_HOSTINGER.md` ya tiene la guía técnica condensada. Aquí va más detallada.

### Paso 1: Comprar/activar el VPS
- En el panel de Hostinger, sección VPS, crea uno nuevo.
- Sistema operativo recomendado: **Ubuntu 22.04 LTS**.
- Anota la **IP del servidor** y la **contraseña root**.

### Paso 2: Conectarte por SSH
Desde tu PC (terminal o PowerShell):
```bash
ssh root@TU-IP-HOSTINGER
```
La primera vez te pedirá confirmar y luego la contraseña.

### Paso 3: Actualizar el sistema e instalar paquetes
```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv nginx git -y
```

### Paso 4: Clonar el repositorio en el servidor
```bash
cd /var/www
git clone https://github.com/harvalmar/PruebaGit1.git
cd PruebaGit1
git checkout claude/dry-construction-cost-calc-LDPUu
cd calculadora_construccion
```

### Paso 5: Crear entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 6: Probar que funciona temporalmente
```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
```
Abre `http://TU-IP-HOSTINGER:5000` en tu navegador → deberías ver la app.

Detén con `Ctrl+C` y sigue.

### Paso 7: Configurar como servicio permanente (systemd)
```bash
nano /etc/systemd/system/calculadora.service
```

Pega esto (ajusta la ruta si la cambiaste):
```ini
[Unit]
Description=Calculadora LSF Flask
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/PruebaGit1/calculadora_construccion
Environment="PATH=/var/www/PruebaGit1/calculadora_construccion/venv/bin"
ExecStart=/var/www/PruebaGit1/calculadora_construccion/venv/bin/gunicorn \
          --workers 2 \
          --bind unix:/var/www/PruebaGit1/calculadora_construccion/calculadora.sock \
          wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Guardar con `Ctrl+O` → `Enter` → `Ctrl+X`.

Habilitar y arrancar:
```bash
chown -R www-data:www-data /var/www/PruebaGit1
systemctl daemon-reload
systemctl enable calculadora
systemctl start calculadora
systemctl status calculadora      # debe decir "active (running)"
```

### Paso 8: Configurar Nginx como reverse proxy
```bash
nano /etc/nginx/sites-available/calculadora
```

Pega:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    # Si no tienes dominio aún, usa:  server_name TU-IP-HOSTINGER;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/PruebaGit1/calculadora_construccion/calculadora.sock;
    }

    location /static/ {
        alias /var/www/PruebaGit1/calculadora_construccion/static/;
    }
}
```

Activar y reiniciar:
```bash
ln -s /etc/nginx/sites-available/calculadora /etc/nginx/sites-enabled/
nginx -t                  # debe decir "syntax is ok" y "test is successful"
systemctl restart nginx
```

### Paso 9: Abrir el firewall
```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw enable
```

### Paso 10: Apuntar tu dominio (opcional)
En el panel DNS de Hostinger, crea un registro **A** que apunte tu dominio a la IP del VPS.

### Paso 11: HTTPS gratis (opcional pero recomendado)
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

🎉 **Listo.** Tu app está corriendo en `https://tu-dominio.com`.

## 6.4 Para actualizar la app después

Cuando edites el código y subas a GitHub:
```bash
ssh root@TU-IP
cd /var/www/PruebaGit1
git pull
systemctl restart calculadora
```

---

## 6.5 ⚠️ Sobre tu API key de Hostinger

Hostinger tiene una **API REST** (https://developers.hostinger.com) pero **NO sirve para correr código Python**. Esa API es para:
- Gestionar dominios automáticamente
- Crear/borrar VPS por código
- Configurar DNS por script
- Manejar facturación

Tu API key **no convierte el hosting compartido en hosting Python**. La única ruta para Flask es el VPS.

---

# 7. Alternativas más fáciles que Hostinger

Si el VPS te parece complejo, hay servicios diseñados específicamente para apps Python:

| Servicio | Plan gratis | Dificultad | Recomendación |
|---|---|---|---|
| **PythonAnywhere** | ✅ Sí (1 web app) | 🟢 Muy fácil | Mejor para empezar y aprender |
| **Render** | ✅ Sí (con limitaciones) | 🟢 Fácil | Muy popular, despliegue desde GitHub |
| **Railway** | ⚠️ Crédito mensual gratis | 🟢 Fácil | Despliegue automático desde GitHub |
| **Fly.io** | ✅ Limitado | 🟡 Intermedio | Bueno para apps globales |
| **Hostinger VPS** | ❌ Pago | 🔴 Más técnico | Si ya pagas, vale la pena |

### Despliegue express en PythonAnywhere

1. Crea cuenta gratis en https://www.pythonanywhere.com
2. `Web → Add a new web app → Flask → Python 3.10`
3. En la pestaña **Files**, sube los archivos de `calculadora_construccion/`.
4. En la pestaña **Web**, en "Code" apunta a `wsgi.py`.
5. Click en el botón verde **Reload**.
6. Tu app vive en `https://tuusuario.pythonanywhere.com` — sin configurar Nginx ni systemd.

### Despliegue express en Render

1. Crea cuenta gratis en https://render.com
2. Conecta tu cuenta de GitHub.
3. `New → Web Service → selecciona PruebaGit1`.
4. Configura:
   - **Root Directory:** `calculadora_construccion`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app`
5. Click en **Create Web Service**. En 2 minutos está online.

---

## 📌 Resumen ejecutivo

| Objetivo | Acción |
|---|---|
| **Probar la app en mi PC** | VS Code + `python app.py` |
| **Editar precios o fórmulas** | Modificar `app.py` (diccionario `PRECIOS`) |
| **Compartir código con alguien** | Pasarle el link de GitHub |
| **Publicar gratis y rápido** | Usar **PythonAnywhere** o **Render** |
| **Publicar en mi Hostinger** | Necesitas plan **VPS** (no compartido) y seguir la sección 6.3 |
| **Tener mi propio dominio** | Comprarlo en Hostinger y apuntar el DNS al servidor |

---

*Documento generado para el proyecto Calculadora LSF — Sistema de costos constructivos para Colombia.*
