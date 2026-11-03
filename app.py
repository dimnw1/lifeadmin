import streamlit as st
import requests
import base64
from PIL import Image
import io

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")
st.write("Загрузите фото официального письма, чека или скриншота — ИИ распознает документ.")

# Получение API ключа из Secrets или ввода
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.text_input("Введите ваш Google Gemini API Key", type="password")

uploaded_file = st.file_uploader("Выберите файл (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный файл", use_container_width=True)
    
    if st.button("🚀 Обработать документ"):
        if not api_key:
            st.warning("Пожалуйста, введите API ключ для продолжения.")
        else:
            try:
                with st.spinner("ИИ анализирует документ через REST API..."):
                    # Конвертируем картинку в байты в формате JPEG
                    buffered = io.BytesIO()
                    # Конвертируем в RGB на случай прозрачности в PNG
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    # Формируем прямой REST API запрос к стабильной модели
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    headers = {
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и краткое содержание."},
                                    {
                                        "inline_data": {
                                            "mime_type": "image/jpeg",
                                            "data": img_base64
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    result_json = response.json()
                    
                    if response.status_code == 200:
                        # Извлекаем текст ответа из структуры JSON
                        content_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("Документ успешно обработан!")
                        st.markdown("### Результат:")
                        st.write(content_text)
                    else:
                        # Показываем понятную ошибку от API, если что-то пойдет не так
                        error_message = result_json.get("error", {}).get("message", response.text)
                        st.error(f"Ошибка API ({response.status_code}): {error_message}")
                        
            except Exception as e:
                st.error(f"Ошибка при обработке запроса: {e}")
