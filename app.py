import streamlit as st
from google import genai
from PIL import Image
import time

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️", layout="centered")

st.title("🛡️ LifeAdmin AI Assistant")
st.write("Загрузите фото документа или чека — ИИ распознает его.")

# Получение API ключа из Streamlit Secrets или ручного ввода
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.text_input("Введите ваш API ключ", type="password")

uploaded_file = st.file_uploader("Выберите файл (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный файл", use_container_width=True)
    
    if st.button("🚀 Обработать документ"):
        if not api_key:
            st.warning("Пожалуйста, укажите API ключ.")
        else:
            try:
                # Инициализация официального клиента нового поколения
                client = genai.Client(api_key=api_key)
                
                response = None
                success = False
                
                # Цикл с обработкой возможных задержек (503 ошибки)
                with st.spinner("Анализ документа с помощью Gemini..."):
                    for attempt in range(3):
                        try:
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=[
                                    image,
                                    "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и содержание."
                                ]
                            )
                            success = True
                            break
                        except Exception as inner_e:
                            if "503" in str(inner_e) and attempt < 2:
                                time.sleep(3)
                                continue
                            else:
                                raise inner_e
                
                if success and response:
                    st.success("Документ успешно обработан!")
                    st.markdown("### Результат:")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"Ошибка выполнения: {e}")
