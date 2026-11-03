import streamlit as st
import requests
import base64
from PIL import Image
import io

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")

# Отладка: проверяем, видит ли Streamlit секреты
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.info(f"Ключ найден в Secrets! Длина ключа: {len(api_key)} символов. Первые символы: {api_key[:5]}...")
else:
    api_key = ""
    st.warning("Внимание: GEMINI_API_KEY не найден в Streamlit Secrets!")

if not api_key:
    api_key = st.text_input("Введите ваш Google Gemini API Key вручную", type="password")

uploaded_file = st.file_uploader("Выберите файл (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный файл", use_container_width=True)
    
    if st.button("🚀 Обработать документ"):
        if not api_key:
            st.error("Пожалуйста, укажите API ключ.")
        else:
            try:
                with st.spinner("Отправка запроса..."):
                    buffered = io.BytesIO()
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    url = f"https://generativelanguage.googleapis.com/v1beta/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    headers = {"Content-Type": "application/json"}
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
                    
                    st.write(f"Статус ответа сервера: {response.status_code}")
                    
                    if response.text:
                        try:
                            res_json = response.json()
                            if response.status_code == 200:
                                text_result = res_json["candidates"][0]["content"]["parts"][0]["text"]
                                st.success("Успешно!")
                                st.write(text_result)
                            else:
                                st.error(f"Ошибка API: {res_json}")
                        except Exception as ex:
                            st.error(f"Не удалось распарсить JSON. Сырой ответ: {response.text}")
                    else:
                        st.error("Сервер вернул пустой ответ (пустое тело). Возможно, ключ заблокирован или неверный формат.")
            except Exception as e:
                st.error(f"Ошибка: {e}")
