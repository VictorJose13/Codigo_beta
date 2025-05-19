#cd "C:\Users\jose_\OneDrive\Área de Trabalho\Poupança - Copia"
#streamlit run simulador_app.py
import streamlit as st
import requests
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Simulador de Investimentos", layout="wide")
st.title("💰 Simulador de Investimentos com Dados Reais")

# Entradas do usuário
valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=1000.0)
aporte_mensal = st.number_input("Aporte mensal (R$)", min_value=0.0, value=200.0)
meses = st.slider("Período do investimento (meses)", min_value=6, max_value=240, value=24)
ticker_acao = st.text_input("Ticker da ação (ex: PETR4, VALE3, ITUB4)", value="PETR4").upper()

# Função para obter taxas econômicas da BrasilAPI
@st.cache
def obter_taxas_economicas():
    url = "https://brasilapi.com.br/api/taxas/v1"
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            taxas = {taxa['nome']: float(taxa['valor']) / 100 for taxa in dados}
            return taxas
    except Exception as e:
        st.warning(f"Erro ao obter taxas econômicas: {e}")
    return {}

# Função para obter o preço atual de uma ação brasileira
@st.cache
def obter_preco_acao(ticker):
    try:
        dados = yf.Ticker(f"{ticker}.SA").history(period="1d")
        return dados['Close'].iloc[-1] if not dados.empty else 0
    except:
        return 0

# Obter taxas econômicas
taxas_economicas = obter_taxas_economicas()
taxa_selic = taxas_economicas.get('Selic', 0.13)
taxa_cdi = taxas_economicas.get('CDI', 0.13)
taxa_ipca = taxas_economicas.get('IPCA', 0.04)

# Conversão de taxas anuais para mensais
def taxa_mensal(taxa_anual):
    return (1 + taxa_anual) ** (1/12) - 1

taxa_selic_mensal = taxa_mensal(taxa_selic)
taxa_cdi_mensal = taxa_mensal(taxa_cdi)
taxa_ipca_mensal = taxa_mensal(taxa_ipca)

# Obter preço da ação
preco_acao = obter_preco_acao(ticker_acao)

# Estimar taxas de retorno mensais
taxas = {
    "Poupança": {"taxa": 0.005, "categoria": "Renda Fixa"},
    "Tesouro Selic": {"taxa": taxa_selic_mensal, "categoria": "Renda Fixa"},
    "CDI": {"taxa": taxa_cdi_mensal, "categoria": "Renda Fixa"},
    "Bitcoin": {"taxa": 0.02, "categoria": "Renda Variável"},
    f"Ação {ticker_acao}": {"taxa": 0.012, "categoria": "Renda Variável"}
}

# Função de simulação
def simular_investimento(valor_inicial, aporte, meses, taxa, inflacao):
    saldo = valor_inicial
    historico_nominal = [saldo]
    historico_real = [saldo]
    for i in range(meses):
        saldo *= (1 + taxa)
        saldo += aporte
        historico_nominal.append(saldo)
        saldo_real = saldo / ((1 + inflacao) ** (i + 1))
        historico_real.append(saldo_real)
    return historico_nominal, historico_real

# Simular investimentos
resultados = {}
for nome, info in taxas.items():
    nominal, real = simular_investimento(valor_inicial, aporte_mensal, meses, info["taxa"], taxa_ipca_mensal)
    resultados[nome] = {
        "nominal": nominal,
        "real": real,
        "categoria": info["categoria"]
    }

# Gráfico interativo com Plotly
fig = go.Figure()
for nome, dados in resultados.items():
    fig.add_trace(go.Scatter(x=list(range(meses + 1)), y=dados["nominal"], mode='lines', name=f"{nome} (Nominal)"))
    fig.add_trace(go.Scatter(x=list(range(meses + 1)), y=dados["real"], mode='lines', name=f"{nome} (Real)", line=dict(dash='dash')))

fig.update_layout(
    title="Evolução dos Investimentos (Nominal vs Real)",
    xaxis_title="Meses",
    yaxis_title="Saldo Acumulado (R$)",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# Exibir resultados finais
st.subheader("📈 Resultados Finais")
investido = valor_inicial + aporte_mensal * meses
for nome, dados in resultados.items():
    saldo_final = dados["nominal"][-1]
    saldo_real = dados["real"][-1]
    lucro = saldo_final - investido
    perc = (lucro / investido) * 100
    st.markdown(f"**{nome}**: Saldo final R$ {saldo_final:,.2f} | Lucro R$ {lucro:,.2f} ({perc:.2f}%) | Saldo Real R$ {saldo_real:,.2f}")

# Rankings por categoria
st.subheader("🏆 Rankings por Categoria (Rentabilidade Real)")
categorias = {"Renda Fixa": [], "Renda Variável": []}
for nome, dados in resultados.items():
    saldo_real = dados["real"][-1]
    rendimento = (saldo_real - investido) / investido
    categorias[dados["categoria"]].append((nome, rendimento, saldo_real))

emojis = ["🥇", "🥈", "🥉"]
for categoria, lista in categorias.items():
    st.markdown(f"### {categoria}")
    lista.sort(key=lambda x: x[1], reverse=True)
    for i, (nome, perc, saldo) in enumerate(lista):
        emoji = emojis[i] if i < len(emojis) else "🔸"
        st.markdown(f"{emoji} **{nome}** — Saldo Real: R$ {saldo:,.2f} | Rentabilidade: {perc * 100:.2f}%")

# Exportar resultados para Excel
st.subheader("📥 Exportar Resultados para Excel")

df_resultado = pd.DataFrame({"Mes": list(range(meses + 1))})
for nome, dados in resultados.items():
    df_resultado[f"{nome} (Nominal)"] = dados["nominal"]
    df_resultado[f"{nome} (Real)"] = dados["real"]

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    df_resultado.to_excel(writer, index=False, sheet_name="Simulação")
excel_buffer.seek(0)

st.download_button(
    label="📥 Baixar resultados em Excel (.xlsx)",
    data=excel_buffer,
    file_name="simulacao_investimentos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)