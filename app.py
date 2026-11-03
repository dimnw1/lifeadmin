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
            
            # Делаем попытки с нарастающей задержкой для обхода 503 ошибки
            for attempt in range(4):
                try:
                    with st.spinner(f"Обработка запроса моделью 3.8-flash (попытка {attempt + 1}/4)..."):
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
                    error_str = str(e)
                    if "503" in error_str and attempt < 3:
                        time.sleep(3 + attempt * 2)  # Увеличиваем паузу: 3 сек, 5 сек, 7 сек
                        continue
                    else:
                        st.error(f"Ошибка: {e}")
                        break
            
            if success and response:
                st.success("Документ успешно обработан!")
                st.markdown("### Результат:")
                st.write(response.text)
