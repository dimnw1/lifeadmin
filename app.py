                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[
                                image,
                                "Распознай этот документ или чек. Выдели ключевые данные: категорию, дату, сумму, организацию и содержание."
                            ]
                        )
