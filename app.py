import streamlit as st
from google import genai
from PIL import Image
import time

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")
st.write("Загрузите фото документа или чека — ИИ распознает его.")

# Получение API ключа
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
            client = genai.Client(api_key=api_key)
            response = None
            success = False
            
            # Делаем до 3 попыток в случае ошибки 503
            for attempt in range(3):
                try:
                    with st.spinner(f"Анализ документа (попытка {attempt + 1}/3)..."):
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[
                                image,
                                "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и содержание."
                            ]
                        )
                        success = True
                        break
                except Exception as e:
                    if "503" in str(e) and attempt < 2:
                        time.sleep(2)  # Ждем 2 секунды перед повтором
                        continue
                    else:
                        st.error(f"Ошибка: {e}")
                        break
            
            if success and response:
                st.success("Документ успешно обработан!")
                st.markdown("### Результат:")
                st.write(response.text)
