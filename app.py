import os
import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="LifeAdmin AI", page_icon="🛡️")

st.title("🛡️ LifeAdmin AI Assistant")
st.write("Загрузите фото официального письма, чека или скриншота подписки — ИИ сам распознает документ и сохранит его.")

# Получение API ключа из Secrets или из инпута
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
                genai.configure(api_key=api_key)
                # Используем стабильную модель для генерации контента
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                with st.spinner("ИИ анализирует документ..."):
                    response = model.generate_content([
                        image,
                        "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и краткое содержание."
                    ])
                    
                st.success("Документ успешно обработан!")
                st.markdown("### Результат:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Ошибка при обращении к ИИ: {e}")
