import openai
import speech_recognition as sr
from playsound import playsound
from pathlib import Path
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

arquivo_audio = "hello.mp3"

recognizer = sr.Recognizer()

def gravar_audio():
    """Captura áudio do microfone e retorna áudio gravado"""

    with sr.Microphone() as source:
        print("Ouvindo...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    
    return audio

def transcrever_audio(audio):
    """Transcreve o áudio utilizando o modelo Whisper"""

    try:
        wav_data = BytesIO(audio.get_wav_data())  # cria o buffer
        wav_data.name = "audio.wav"               # nome fake para o arquivo
        wav_data.seek(0)                          # garante ponteiro no início

        transcricao = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_data
        )
        return transcricao.text
    except Exception as e:
        print("Erro ao transcrever áudio:", str(e))
        return ""


def completa_texto(mensagens):
    """Gera uma resposta com base no histórico de mensagens usando GPT 3.5"""

    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=mensagens,
            max_tokens=1000,
            temperature=0
        )
        return resposta.choices[0].message.content
    except Exception as e:
        print("Erro na geração da resposta:", str(e))
        return "Desculpe, não consegui entender."
    
def criar_audio(texto):
    """Cria um arquivo de áudio a partir do texto utilizando a API do TTS"""

    if Path(arquivo_audio).exists():
        Path(arquivo_audio).unlink()

    try:
        resposta = client.audio.speech.create(
            model="tts-1",
            voice="echo",
            input=texto
        )

        resposta.write_to_file(arquivo_audio)
    except Exception as e:
        print(f"Erro ao criar áudio:", str(e))

def rodar_audio():
    """Reproduz o arquivo de áudio gerado"""

    if Path(arquivo_audio).exists():
        playsound(arquivo_audio)
    else:
        print("Arquivo de áudio não encontrado.")

def main():
    """Função principal para executar o assistente de voz"""

    mensagens = []

    while True:
        audio = gravar_audio()
        transcricao = transcrever_audio(audio)

        if not transcricao:
            print("Não foi possível transcrever o áudio. Tente novamente.")
            continue

        mensagens.append({"role": "user", "content": transcricao})
        print(f"Usuário: {mensagens[-1]['content']}")

        resposta_texto = completa_texto(mensagens)
        mensagens.append({"role": "assistant", "content": resposta_texto})
        print(f"Assistente: {mensagens[-1]['content']}")

        criar_audio(resposta_texto)
        rodar_audio()

if __name__ == "__main__":
    main()