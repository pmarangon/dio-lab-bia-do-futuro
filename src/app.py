import json
import streamlit as st
import pandas as pd
import requests
import re

#==== CONFIGURAÇÃO ====
OLAMA_URL = 'http://localhost:11434/api/generate'
MODELO = "gemma:2b"
BING_API_KEY = " 8GLgd2hqJScbRXgy511MXAck"

###### CARREGAR DADOS ######
with open('../data/perfil_investidor.json', 'r', encoding='utf-8') as f:
    perfil = json.load(f)

transacoes = pd.read_csv('../data/transacoes.csv')
historico = pd.read_csv('../data/historico_atendimento.csv')

with open('../data/produtos_financeiros.json', 'r', encoding='utf-8') as f:
    produtos = json.load(f)

#==== INTERFACE ====
st.title("Frank - Assistente Financeiro")
st.write(f"CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}")
st.write(f"PROFISSÃO: {perfil['profissao']} | RENDA MENSAL: R${perfil['renda_mensal']:,.2f}")
st.write(f"OBJETIVO: {perfil['objetivo_principal']}")
st.write(f"PATRIMONIO: R${perfil['patrimonio_total']:,.2f} | RESERVA: R${perfil['reserva_emergencia_atual']:,.2f}")

st.write("TRANSACOES RECENTES:")
df_transacoes = transacoes.copy()
if 'valor' in df_transacoes.columns:
    df_transacoes['valor'] = df_transacoes['valor'].apply(lambda v: f"R${v:,.2f}")
st.dataframe(df_transacoes)

st.write("ATENDIMENTOS ANTERIORES:")
st.dataframe(historico)

st.write("PRODUTOS DISPONÍVEIS:")
df_produtos = pd.DataFrame(produtos)
df_produtos['aporte_minimo'] = df_produtos['aporte_minimo'].apply(lambda v: f"R${v:,.2f}")

def color_risco(val):
    if val == 'baixo':
        return 'color: green; font-weight: bold;'
    elif val == 'medio':
        return 'color: orange; font-weight: bold;'
    elif val == 'alto':
        return 'color: red; font-weight: bold;'
    return ''

styled_df = df_produtos.style.applymap(color_risco, subset=['risco'])
st.dataframe(styled_df, use_container_width=True)

#==== API DE CÂMBIO ====
def cotacao_moeda(base="USD", destino="BRL"):
    try:
        url = f"https://economia.awesomeapi.com.br/json/last/{base}-{destino}"
        r = requests.get(url)
        data = r.json()
        chave = f"{base}{destino}"
        valor = data[chave]["bid"]
        return f"A cotação {base}/{destino} hoje está em R${float(valor):.2f}"
    except Exception:
        return f"Não consegui obter a cotação de {base}/{destino} agora."

#==== API DE CRIPTOMOEDAS ====
def cotacao_crypto(cripto):
    try:
        cripto = cripto.lower().strip()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies=brl"
        r = requests.get(url)
        data = r.json()
        if cripto in data:
            valor = data[cripto]["brl"]
            return f"O preço do {cripto.capitalize()} hoje está em R${float(valor):,.2f}"
        else:
            return f"Não encontrei a criptomoeda '{cripto}' na CoinGecko."
    except Exception:
        return f"Não consegui obter o preço da criptomoeda {cripto} agora."

#==== PESQUISA WEB ====
def pesquisa_web(query):
    try:
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
        params = {"q": query, "mkt": "pt-BR"}
        r = requests.get(url, headers=headers, params=params)
        data = r.json()

        resultados = []
        for item in data.get("webPages", {}).get("value", [])[:3]:
            resultados.append(f"- {item['name']}: {item['snippet']}")

        if resultados:
            return "Aqui está o que encontrei na web:\n" + "\n".join(resultados)
        else:
            return "Não encontrei informações relevantes na web."
    except Exception:
        return "Não consegui pesquisar na web agora."

#==== FUNÇÃO PRINCIPAL ====
def perguntar(msg):
    texto = msg.lower()

    # Detecta moedas tradicionais
    moedas = {
        "dólar": "USD",
        "dolar": "USD",
        "usd": "USD",
        "euro": "EUR",
        "eur": "EUR",
        "libra": "GBP",
        "gbp": "GBP",
        "peso": "ARS",
        "ars": "ARS"
    }
    for palavra, codigo in moedas.items():
        if palavra in texto:
            return cotacao_moeda(codigo, "BRL")

    # Detecta criptomoedas
    if "cripto" in texto or "criptomoeda" in texto:
        return "Qual criptomoeda você gostaria de consultar? Exemplo: Bitcoin, Ethereum, Cardano, Solana."

    match = re.search(r"(bitcoin|ethereum|cardano|solana|polkadot|dogecoin|shiba|litecoin|tron|avalanche)", texto)
    if match:
        return cotacao_crypto(match.group(1))

    # Detecta CDB
    if "cdb" in texto:
        return (
            "O CDB (Certificado de Depósito Bancário) é um título emitido por bancos para captar recursos. "
            "Você empresta dinheiro ao banco e recebe juros em troca. Existem CDBs de liquidez diária, "
            "que permitem resgate a qualquer momento, e CDBs com prazo fixo. É um investimento de renda fixa, "
            "com baixo risco e protegido pelo FGC até R$250 mil por CPF e instituição."
        )

    # Detecta LCI/LCA
    if "lci" in texto or "lca" in texto:
        return (
            "LCI (Letra de Crédito Imobiliário) e LCA (Letra de Crédito do Agronegócio) são títulos de renda fixa "
            "emitidos por bancos para financiar o setor imobiliário e agrícola. O grande diferencial é que são "
            "isentos de Imposto de Renda para pessoas físicas. Também contam com a proteção do FGC até R$250 mil."
        )

    # Detecta Tesouro Selic
    if "tesouro selic" in texto:
        return (
            "O Tesouro Selic é um título público emitido pelo governo federal. É considerado o investimento mais seguro "
            "do país e indicado para reserva de emergência, pois acompanha a taxa Selic e tem liquidez diária."
        )

    # Detecta Fundos Multimercado
    if "fundo multimercado" in texto or "multimercado" in texto:
        return (
            "Fundos multimercado são carteiras que podem investir em diferentes ativos: renda fixa, ações, câmbio, "
            "entre outros. Eles oferecem diversificação e podem ter diferentes níveis de risco, desde conservadores até arrojados."
        )

    # Detecta previdência privada
    if "previdência" in texto or "previdencia" in texto:
        return (
            "A previdência privada é um investimento de longo prazo voltado para aposentadoria. "
            "Existem dois tipos principais: PGBL (vantajoso para quem declara IR completo) e VGBL "
            "(para quem declara IR simplificado). Ela permite acumular recursos ao longo do tempo, "
            "com benefícios fiscais dependendo do perfil do investidor. "
            "É indicada para quem busca complementar a aposentadoria pública."
        )

    # Caso não seja câmbio, cripto ou produtos específicos, pesquisa na web
    resultado_web = pesquisa_web(msg)
    if "Não encontrei" in resultado_web:
        return (
            "Não achei informações recentes na web, mas aqui vão algumas opções clássicas para começar a investir:\n"
            "- Tesouro Selic (seguro e indicado para reserva de emergência)\n"
            "- CDB de liquidez diária (renda fixa com baixo risco)\n"
            "- Fundos multimercado conservadores\n"
            "- Previdência privada (PGBL ou VGBL, dependendo da sua declaração de IR)\n"
            "Esses são pontos de partida comuns para iniciantes."
        )
    return resultado_web

#==== CHAT ====
st.write("Olá! Sou o Frank, seu assistente financeiro pessoal. Como posso ajudar você?")
if pergunta := st.chat_input("Faça sua pergunta sobre suas finanças:"):
    resposta = perguntar(pergunta)
    with st.spinner("..."):
        st.chat_message("assistant").markdown(resposta)