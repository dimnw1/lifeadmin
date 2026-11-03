import streamlit as st
import requests
import base64
from PIL import Image
import io

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")
st.write("Загрузите фото документа или чека — ИИ распознает его.")

# Получение API ключа
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.text_input("Введите ваш Google Gemini API Key", type="password")

uploaded_file = st.file_uploader("Выберите файл (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный файл", use_container_width=True)
    
    if st.button("🚀 Обработать документ"):
        if not api_key:
            st.warning("Пожалуйста, введите API ключ.")
        else:
            try:
                with st.spinner("Отправка запроса в Gemini..."):
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
                    
                    # Проверяем, есть ли вообще текст в ответе
                    if not response.text:
                        st.error("Ошибка: Сервер Google вернул абсолютно пустой ответ. Проверьте правильность API ключа.")
                    else:
                        try:
                            result_json = response.json()
                        except Exception:
                            st.error(f"Ошибка: Сервер вернул не JSON. Текст ответа: {response.text}")
                            result_json = None
                        
                        if result_json and response.status_code == 200:
                            try:
                                content_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
                                st.success("Документ успешно обработан!")
                                st.markdown("### Результат:")
                                st.write(content_text)
                            except (KeyError, IndexError) as ke:
                                st.error(f"Необычный формат ответа от Google: {result_json}")
                        elif result_json:
                            error_message = result_json.get("error", {}).get("message", response.text)
                            st.error(f"Ошибка API ({response.status_code}): {error_message}")
                            
            except Exception as e:
                st.error(f"Системная ошибка: {e}")
