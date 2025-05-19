import requests
import yfinance as yf
import matplotlib.pyplot as plt

# Função para obter a taxa Selic atual
def obter_taxa_selic():
    url = "https://brasilapi.com.br/api/taxas/v1"
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            for taxa in dados:
                if taxa['nome'] == 'Selic':
                    return float(taxa['valor']) / 100  # Convertendo de % para decimal
    except Exception as e:
        print(f"Erro ao obter taxa Selic: {e}")
    return 0.08  # Valor padrão anual

# Função para obter o preço atual do Bitcoin em BRL
def obter_preco_bitcoin():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl"
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados['bitcoin']['brl']
    except Exception as e:
        print(f"Erro ao obter preço do Bitcoin: {e}")
    return 0

# Função para obter o preço atual de uma ação brasileira
def obter_preco_acao(ticker):
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        dados = acao.history(period="1d")
        if not dados.empty:
            return dados['Close'].iloc[-1]
    except Exception as e:
        print(f"Erro ao obter preço da ação {ticker}: {e}")
    return 0

# Função para simular crescimento de investimento
def simular_investimento(valor_inicial, aporte_mensal, meses, taxa_juros, inflacao_mensal=0.0):
    saldo = valor_inicial
    historico_nominal = [saldo]
    historico_real = [saldo]
    for _ in range(meses):
        saldo *= (1 + taxa_juros)
        saldo += aporte_mensal
        historico_nominal.append(saldo)
        saldo_real = saldo / ((1 + inflacao_mensal) ** (_ + 1))
        historico_real.append(saldo_real)
    return historico_nominal, historico_real

# Entradas do usuário
valor_inicial = float(input("Digite o valor inicial (R$): "))
aporte_mensal = float(input("Digite o aporte mensal (R$): "))
meses = int(input("Digite o período do investimento em meses: "))
ticker_acao = input("Digite o ticker da ação desejada (ex: PETR4, VALE3, ITUB4): ").upper()

# Obter dados atualizados
taxa_selic = obter_taxa_selic()
preco_bitcoin = obter_preco_bitcoin()
preco_acao = obter_preco_acao(ticker_acao)

# Taxas médias estimadas
taxas = {
    "Poupança": 0.005,
    "Tesouro Selic": taxa_selic / 12,
    "Bitcoin": 0.02,
    f"Ação {ticker_acao}": 0.012
}

# Simular inflação (ex: 4% ao ano)
inflacao_anual = 0.04
inflacao_mensal = (1 + inflacao_anual) ** (1/12) - 1

# Simular investimentos
resultados_nominais = {}
resultados_reais = {}
rendimentos_finais = {}

for investimento, taxa in taxas.items():
    nominal, real = simular_investimento(valor_inicial, aporte_mensal, meses, taxa, inflacao_mensal)
    resultados_nominais[investimento] = nominal
    resultados_reais[investimento] = real
    rendimento_total = nominal[-1] - (valor_inicial + aporte_mensal * meses)
    rendimento_percentual = (nominal[-1] / (valor_inicial + aporte_mensal * meses) - 1) * 100
    rendimentos_finais[investimento] = (rendimento_total, rendimento_percentual)

# Mostrar rendimentos finais
print("\nResumo Final (nominal):")
for inv, (lucro, perc) in rendimentos_finais.items():
    print(f"{inv}: Lucro de R$ {lucro:.2f} ({perc:.2f}%)")

# Plotar gráfico
plt.figure(figsize=(12, 6))
for investimento in taxas.keys():
    plt.plot(resultados_nominais[investimento], label=f"{investimento} (Nominal)")
    plt.plot(resultados_reais[investimento], linestyle='--', label=f"{investimento} (Real)")

plt.title("Simulação de Investimentos: Nominal vs Real")
plt.xlabel("Meses")
plt.ylabel("Saldo (R$)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
