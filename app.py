import streamlit as st
from google import genai
from PIL import Image

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
            try:
                with st.spinner("Анализ документа через новый SDK..."):
                    # Инициализация современного клиента Google GenAI
                    client = genai.Client(api_key=api_key)
                    
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[
                            image,
                            "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и содержание."
                        ]
                    )
                    
                    st.success("Документ успешно обработан!")
                    st.markdown("### Результат:")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"Ошибка: {e}")
