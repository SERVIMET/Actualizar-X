from datetime import datetime
import os
import re
from PIL import Image, ImageDraw, ImageFont
import requests
import tweepy

# 1. Descargar la página web de la estación de Talcahuano
URL = "http://web.directemar.cl/met/jturno/estaciones/talcahuano/index.htm"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
  response = requests.get(URL, headers=headers, timeout=15)
  response.encoding = "iso-8859-1"  # Codificación habitual en estas páginas
  html_content = response.text
except Exception as e:
  print(f"Error al descargar la web: {e}")
  html_content = ""


# Función auxiliar para buscar valores en el texto usando expresiones regulares
def extraer_dato(patron, texto, por_defecto="--"):
  match = re.search(patron, texto)
  if match:
    return match.group(1).strip()
  return por_defecto


# Capturamos los valores clave del HTML
temp_actual = extraer_dato(r"Temperatura.*?([\d\.,]+)", html_content, "12.0")
humedad = extraer_dato(r"Humedad.*?([\d]+)", html_content, "82")
viento_vel = extraer_dato(r"Viento.*?([\d\.,]+)", html_content, "12.8")
presion_rel = extraer_dato(r"Presion.*?([\d\.,]+)", html_content, "1014.5")

print(
    f"Datos extraídos -> Temp: {temp_actual}, Humedad: {humedad}, Viento:"
    f" {viento_vel}"
)

# 2. Generar la imagen con Pillow
try:
  img = Image.open("fondo_talcahuano.jpg")
except FileNotFoundError:
  print("No se encontró la imagen de fondo. Usando fondo negro por defecto.")
  img = Image.new("RGB", (1000, 1200), color=(15, 23, 42))

draw = ImageDraw.Draw(img)

# Usar fuente por defecto o cargar una si la incluyes en el repositorio
try:
  font_titulo = ImageFont.truetype("Roboto-Bold.ttf", 40)
  font_dato = ImageFont.truetype("Roboto-Bold.ttf", 60)
  font_texto = ImageFont.truetype("Roboto-Regular.ttf", 22)
except:
  font_titulo = font_dato = font_texto = ImageFont.load_default()

# Textos (sin tildes según tus indicaciones anteriores)
draw.text((50, 70), "TALCAHUANO", fill=(255, 255, 255), font=font_titulo)

# Fecha y hora actual (sin tildes en los días/meses)
ahora = datetime.now().strftime("%d de %b de %Y | %H:%M")
draw.text(
    (50, 130),
    f"Fecha y hora: {ahora}".replace("á", "a")
    .replace("é", "e")
    .replace("í", "i")
    .replace("ó", "o")
    .replace("ú", "u"),
    fill=(255, 255, 255),
    font=font_texto,
)

# Dibujar temperatura actual
draw.text(
    (80, 250), f"{temp_actual} C", fill=(255, 255, 255), font=font_dato
)

imagen_path = "reporte_talcahuano.png"
img.save(imagen_path)

# 3. Publicar en X (Twitter) usando Tweepy Client (API v2) y OAuth 1.0a para multimedia
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

if API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_TOKEN_SECRET:
  try:
    # Cliente para la API v2 (para enviar el tuit)
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )

    # API v1.1 necesaria exclusivamente para subir la imagen multimedia
    auth = tweepy.OAuth1UserHandler(
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )
    api_v1 = tweepy.API(auth)

    mensaje = "Reporte meteorologico automatico - Estacion Talcahuano."

    # Subir la imagen usando la API v1.1
    media = api_v1.media_upload(imagen_path)

    # Publicar el tuit con la imagen adjunta usando la API v2
    client.create_tweet(text=mensaje, media_ids=[media.media_id])
    print("¡Reporte publicado con exito en X!")
  except Exception as e:
    print(f"Error al publicar en X: {e}")
else:
  print(
      "Faltan las credenciales de la API de X en las variables de entorno"
      " (Secrets)."
  )
