import ollama

def interpret_with_local_ai(prompt_text, model="mistral"):
    """
    Wywołuje lokalny model Ollama i zwraca interpretację tekstową.
    Model domyślny: mistral (zalecany przy 16 GB RAM).
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś ekspertem analizującym dane graczy i wykresy z gier komputerowych. Odpowiadaj po polsku, rzeczowo, jasno i zwięźle."
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"[Błąd AI]: {e}"

