import yfinance as yf
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

def retorna_cotacao(ticker, periodo):
    ticker_obj_function = yf.Ticker(f"{ticker}.SA")
    hist = ticker_obj_function.history(period=periodo)["Close"]
    hist.index = hist.index.strftime("%Y-%m-%d")
    hist = round(hist, 2)

    if len(hist) > 30:
        slice_size = int(len(hist) / 30)
        hist = hist[::-slice_size][::-1]

    return hist.to_json()

tools = [
    {
        "type": "function",
        "function": {
            "name": "retorna_cotacao",
            "description": "Retorna a cotação de ações da Ibovespa",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker":{
                        "type": "string",
                        'description': "O ticker da ação. Ex.: BBAS3, BBDC4, etc"
                    },
                    "periodo": {
                        "type": "string",
                        "description": "Período retornado dos dados históricos da cotação \
                                       sendo '1mo' equivale a um mês, '1d' equivale a 1 dia \
                                       e '1y' equivale a 1 ano e 'ytd' equivale a todos os tempos",
                        "enum": ["1d", "5d", "1mo", "6mo", "1y", "5y", "10y", "ytd", "max"]
                    }
                }
            }
        }
    }
]

funcao_disponivel = {"retorna_cotacao": retorna_cotacao}

mensagens = [{"role": "user", "content": "Qual é a cotação da Vale no último ano?"}]

resposta = client.chat.completions.create(
    messages=mensagens,
    model="gpt-3.5-turbo-0125",
    tools=tools,
    tool_choice="auto"
)

tool_calls = resposta.choices[0].message.tool_calls
# print(tool_calls)

if tool_calls:
    mensagens.append(resposta.choices[0].message)

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = funcao_disponivel[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_return = function_to_call(**function_args)

        mensagens.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_return
        })

        segunda_resposta = client.chat.completions.create(
            messages=mensagens,
            model="gpt-3.5-turbo-0125",
        )

        mensagens.append(segunda_resposta.choices[0].message)
        print(segunda_resposta.choices[0].message.content)