import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
import openai
import speech_recognition as sr
from playsound import playsound

# ========= Config =========
ARQUIVO_AUDIO = "hello.mp3"
CALIBRACAO_SEG = 0.3     # reduzir no macOS para evitar threshold alto demais
TIMEOUT_INICIO = 5       # tempo máximo esperando você começar a falar
LIMITE_FALA = 15         # tempo máximo de cada fala
AMOSTRAGEM = 16000       # taxa fixa ajuda no macOS
ENERGY_BASE = 300
PAUSE_THRESHOLD = 0.8    # silêncio curto encerra a frase
# Permite forçar um dispositivo específico via env (ex.: INPUT_DEVICE_INDEX=2)
INPUT_DEVICE_INDEX = os.getenv("INPUT_DEVICE_INDEX")

# ========= Setup =========
load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = ENERGY_BASE
recognizer.pause_threshold = PAUSE_THRESHOLD


# ========= Áudio (entrada) =========
def _pick_input_device():
    """
    Seleciona um microfone funcional.
    - Se INPUT_DEVICE_INDEX estiver definido, tenta usá-lo.
    - Senão, procura por um dispositivo "provável" e testável.
    Retorna o índice do dispositivo ou None.
    """
    try:
        names = sr.Microphone.list_microphone_names()
    except OSError:
        return None

    if not names:
        return None

    # Força via env?
    if INPUT_DEVICE_INDEX is not None:
        try:
            idx = int(INPUT_DEVICE_INDEX)
            # Testa abrir
            with sr.Microphone(device_index=idx):
                return idx
        except Exception:
            print(f"[WARN] INPUT_DEVICE_INDEX={INPUT_DEVICE_INDEX} inválido ou inacessível.")

    preferred_keywords = ["microphone", "mic", "input", "line in", "usb", "built-in"]
    preferred = [i for i, n in enumerate(names) if any(k in n.lower() for k in preferred_keywords)]
    candidates = preferred if preferred else list(range(len(names)))

    for idx in candidates:
        try:
            with sr.Microphone(device_index=idx):
                return idx
        except Exception:
            continue
    return None


def gravar_audio():
    """
    Captura áudio do microfone e retorna um objeto AudioData do speech_recognition.
    Usa timeouts para não travar indefinidamente.
    """
    device_index = _pick_input_device()
    if device_index is None:
        raise RuntimeError(
            "Nenhum microfone disponível. Verifique: "
            "1) Permissão de microfone para o Terminal/iTerm; "
            "2) Entrada de Som no macOS; "
            "3) PortAudio/PyAudio instalados corretamente."
        )

    with sr.Microphone(device_index=device_index, sample_rate=AMOSTRAGEM) as source:
        print(f"Ouvindo... (dispositivo {device_index})")
        recognizer.adjust_for_ambient_noise(source, duration=CALIBRACAO_SEG)
        try:
            audio = recognizer.listen(source, timeout=TIMEOUT_INICIO, phrase_time_limit=LIMITE_FALA)
        except sr.WaitTimeoutError:
            print("Ninguém falou nos primeiros segundos. Tentando novamente...")
            return None
    return audio


# ========= STT (Whisper) =========
def transcrever_audio(audio):
    """Transcreve o áudio utilizando Whisper."""
    try:
        wav_data = BytesIO(audio.get_wav_data())
        wav_data.name = "audio.wav"
        wav_data.seek(0)

        transcricao = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_data
        )
        return (transcricao.text or "").strip()
    except Exception as e:
        print("Erro ao transcrever áudio:", str(e))
        return ""


# ========= Chat (GPT) =========
def completa_texto(mensagens):
    """Gera uma resposta com base no histórico de mensagens."""
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


# ========= TTS (voz) =========
def criar_audio(texto):
    """Cria arquivo de áudio a partir do texto utilizando TTS."""
    try:
        p = Path(ARQUIVO_AUDIO)
        if p.exists():
            p.unlink()

        resposta = client.audio.speech.create(
            model="tts-1",
            voice="echo",
            input=texto
        )
        resposta.write_to_file(ARQUIVO_AUDIO)
    except Exception as e:
        print("Erro ao criar áudio:", str(e))


def rodar_audio():
    """Reproduz o arquivo de áudio gerado."""
    p = Path(ARQUIVO_AUDIO)
    if p.exists():
        try:
            playsound(str(p))
        except Exception as e:
            print("Erro ao reproduzir áudio:", str(e))
    else:
        print("Arquivo de áudio não encontrado.")


# ========= App =========
def main():
    """Executa o assistente de voz."""
    mensagens = []
    print("[INFO] Se travar em 'Ouvindo...', confira permissões do microfone nas Preferências do macOS.")

    try:
        while True:
            audio = gravar_audio()
            if audio is None:
                continue

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

    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")


if __name__ == "__main__":
    main()
