import json
import sqlite3
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ (SQLite) ---
DB_NAME = 'lifeadmin.db'


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Таблица для документов/штрафов
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, summary TEXT, amount REAL, deadline TEXT, status TEXT DEFAULT 'active'
        )
    ''')
  # Таблица для подписок
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT, cost REAL, currency TEXT, renewal_date TEXT, status TEXT DEFAULT 'active'
        )
    ''')
  # Таблица для чеков/гарантий
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT, item_name TEXT, amount REAL, warranty_expiry_date TEXT
        )
    ''')
  conn.commit()
  conn.close()


init_db()

# --- 2. СИСТЕМНЫЙ ПРОМПТ ИИ ---
SYSTEM_PROMPT = """
Ты — интеллектуальный анализатор данных для мобильного приложения LifeAdmin. Твоя задача — проанализировать предоставленное пользователем изображение (это может быть чек, официальное письмо/штраф или скриншот подписки), определить тип документа и вернуть данные строго в формате JSON.

1. ОПРЕДЕЛИ КАТЕГОРИЮ (`category`):
- "document" — если это официальное письмо, штраф, налоговое уведомление или бюрократический документ.
- "subscription" — если это подтверждение подписки, квитанция от цифрового сервиса или уведомление о пробном периоде.
- "receipt" — если это чек из магазина на покупку физического товара с гарантией.

2. СТРУКТУРА ОТВЕТА:
Верни ответ ИСКЛЮЧИТЕЛЬНО в формате чистого JSON (без обрамления в ```json и без каких-либо вводных слов от себя). 

Схема JSON:
{
  "category": "document" | "subscription" | "receipt",
  "language_detected": "код языка текста (например, 'ru', 'ro', 'en')",
  "data": {
    "title": "Название документа (если category == document, иначе null)",
    "summary": "Перевод/суть и инструкция (если category == document, иначе null)",
    "amount": 0.0, 
    "deadline": "YYYY-MM-DD или null",

    "service_name": "Название сервиса (если category == subscription, иначе null)",
    "cost": 0.0,
    "currency": "USD/EUR/MDL и т.д.",
    "renewal_date": "YYYY-MM-DD или null",
    "cancellation_url": "Подсказка, как отменить или null",

    "store_name": "Название магазина (если category == receipt, иначе null)",
    "item_name": "Название товара (если category == receipt, иначе null)",
    "warranty_expiry_date": "YYYY-MM-DD или null"
  }
}
"""


# --- 3. ФУНКЦИЯ ОБРАБОТКИ ЧЕРЕЗ ИИ ---
def process_image_with_ai(image: Image.Image, api_key: str):
  # Инициализируем клиент Google GenAI
  client = genai.Client(api_key=api_key)

  try:
    # Отправляем фото и системный промпт модели Gemini 1.5 Flash
    response = client.models.generate_content(
        model='gemini-1.5-flash-002',
        contents=[image, 'Проанализируй этот файл и верни JSON по инструкции.'],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,  # Минимальная креативность для точности данных
        ),
    )

    # Очищаем текст от возможных лишних символов маркдауна
    raw_text = response.text.strip()
    if raw_text.startswith('```json'):
      raw_text = raw_text[7:]
    if raw_text.endswith('```'):
      raw_text = raw_text[:-3]

    return json.loads(raw_text.strip())
  except Exception as e:
    st.error(f'Ошибка при обращении к ИИ или парсинге JSON: {e}')
    return None


# --- 4. СОХРАНЕНИЕ В БАЗУ ДАННЫХ ---
def save_to_db(parsed_result):
  category = parsed_result.get('category')
  data = parsed_result.get('data', {})

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  if category == 'document':
    cursor.execute(
        'INSERT INTO documents (title, summary, amount, deadline) VALUES (?, ?,'
        ' ?, ?)',
        (
            data.get('title'),
            data.get('summary'),
            data.get('amount'),
            data.get('deadline'),
        ),
    )
  elif category == 'subscription':
    cursor.execute(
        'INSERT INTO subscriptions (service_name, cost, currency,'
        ' renewal_date) VALUES (?, ?, ?, ?)',
        (
            data.get('service_name'),
            data.get('cost'),
            data.get('currency'),
            data.get('renewal_date'),
        ),
    )
  elif category == 'receipt':
    cursor.execute(
        'INSERT INTO receipts (store_name, item_name, amount,'
        ' warranty_expiry_date) VALUES (?, ?, ?, ?)',
        (
            data.get('store_name'),
            data.get('item_name'),
            data.get('amount'),
            data.get('warranty_expiry_date'),
        ),
    )

  conn.commit()
  conn.close()


# --- 5. ИНТЕРФЕЙС STREAMLIT ---
st.title('🛡 LifeAdmin AI Assistant')
st.write(
    'Загрузите фото официального письма, чека или скриншота подписки — ИИ сам'
    ' распознает документ и сохранит его.'
)

# Поле для ввода API-ключа (в реальном приложении убирается в secrets.toml)
api_key_input = st.text_input(
    'Введите ваш Google Gemini API Key', type='password'
)

uploaded_file = st.file_uploader(
    'Выберите файл (PNG, JPG, JPEG)', type=['png', 'jpg', 'jpeg']
)

if uploaded_file and api_key_input:
  image = Image.open(uploaded_file)
  st.image(image, caption='Загруженный файл', use_column_width=True)

  if st.button('🚀 Обработать документ'):
    with st.spinner('ИИ анализирует документ...'):
      result = process_image_with_ai(image, api_key_input)

      if result:
        st.success('Успешно распознано!')
        cat = result.get('category')
        st.info(
            f'Определенная категория: **{cat.upper()}** (Язык:'
            f" {result.get('language_detected')})"
        )

        # Сохраняем в БД
        save_to_db(result)
        st.write('📦 Данные успешно записаны в базу данных SQLite!')

        # Выводим структурированные данные на экран
        st.json(result)
elif uploaded_file and not api_key_input:
  st.warning('Пожалуйста, введите API ключ для продолжения.')
