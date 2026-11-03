import streamlit as st
import requests
import base64
from PIL import Image
import io

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")

# Получение ключа из Secrets
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.text_input("Введите ваш токен AQ...", type="password")

uploaded_file = st.file_uploader("Выберите файл (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный файл", use_container_width=True)
    
    if st.button("🚀 Обработать документ"):
        if not api_key:
            st.error("Пожалуйста, укажите токен.")
        else:
            try:
                with st.spinner("Отправка запроса с новым токеном..."):
                    buffered = io.BytesIO()
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    # Эндпоинт для работы с моделями через Bearer-токен
                    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                    
                    # Передаем токен AQ в заголовке Authorization
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и содержание."},
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
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        text_result = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("Документ успешно обработан!")
                        st.markdown("### Результат:")
                        st.write(text_result)
                    else:
                        st.error(f"Ошибка API ({response.status_code}): {response.text}")
                        
            except Exception as e:
                st.error(f"Ошибка: {e}")
