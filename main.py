import os
import feedparser
import google.generativeai as genai
import asyncio
import edge_tts
from datetime import datetime
import pytz
from xml.sax.saxutils import escape
import re
import urllib.request

# --- CONFIGURAÇÕES DO USUÁRIO ---
GITHUB_USER = "yurileonardos"
REPO_NAME = "meu-podcast-diario"
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}"

# --- FONTES COMPLETAS (Nexo, Valor, ONU, etc) ---
FEEDS = {
    "GOIÁS (Política, Cotidiano)": [
        "https://g1.globo.com/rss/g1/goias/",
        "https://www.jornalopcao.com.br/feed/",
        "https://www.maisgoias.com.br/feed/",
        "https://opopular.com.br/rss",
        "https://diariodegoias.com.br/feed/",
        "https://ohoje.com/feed/"
    ],
    "ESPORTES (Vila Nova & Cruzeiro)": [
        "https://ge.globo.com/rss/ge/futebol/times/vila-nova/",   
        "https://ge.globo.com/rss/ge/futebol/times/cruzeiro/",
        "https://www.maisgoias.com.br/category/esportes/vila-nova/feed/"
    ],
    "CONCURSOS": [
        "https://g1.globo.com/rss/g1/concursos-e-emprego/",
        "https://jcconcursos.com.br/rss/noticias",
        "https://www.pciconcursos.com.br/feed"
    ],
    "BRASIL (Política, Economia, Social)": [
        "https://pox.globo.com/rss/valor", 
        "https://www.nexojornal.com.br/rss.xml",
        "https://exame.com/feed/", 
        "https://istoe.com.br/feed", 
        "https://abes-dn.org.br/feed/", 
        "https://www.opovo.com.br/rss/", 
        "https://feeds.folha.uol.com.br/poder/rss091.xml",
        "https://www.estadao.com.br/rss/politica",
        "https://www.cnnbrasil.com.br/feed/",
        "https://cartacapital.com.br/feed/",
        "https://agenciabrasil.ebc.com.br/rss/ultimas-noticias/feed.xml",
        "https://www.camara.leg.br/noticias/rss/ultimas-noticias",
        "https://www12.senado.leg.br/noticias/feed/todas/rss"
    ],
    "MUNDO (Geopolítica Global)": [
        "https://news.un.org/feed/subscribe/pt/news/all/rss.xml", 
        "https://brasil.elpais.com/rss/elpais/america.xml",      
        "https://www.bbc.com/portuguese/index.xml",              
        "https://rss.dw.com/xml/rss-br-all",                     
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 
        "https://www.theguardian.com/world/rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.lemonde.fr/rss/une.xml",
        "https://pt.euronews.com/rss?format=xml"
    ],
    "CIÊNCIA, TECNOLOGIA E SAÚDE": [
        "https://super.abril.com.br/feed/",
        "https://gizmodo.uol.com.br/feed/",
        "https://www.nature.com/nature.rss",
        "https://saude.abril.com.br/feed/"
    ],
    "YOUTUBE (Destaques)": [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCO6j6cqBhi2TWVxfcn6t23w", 
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC6w8cK5C5QZJ9J9J9J9J9J9" 
    ]
}

# --- LINKS ESPECIAIS (HTML) ---
WEATHER_URLS = [
    "https://portal.inmet.gov.br/", 
    "https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/88/goiania-go",
    "https://www.terra.com.br/noticias/"
]

def get_data_ptbr():
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
    meses = ['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    return f"{now.day} de {meses[now.month]}, uma {dias[now.weekday()]}"

def get_custom_data():
    text_data = "\n--- DADOS EXTRAS (CLIMA/TERRA) ---\n"
    print("Consultando INMET e Terra...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in WEATHER_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                clean = re.sub(r'<[^>]+>', ' ', html)
                clean = re.sub(r'\s+', ' ', clean)
                text_data += f"Fonte ({url}): {clean[:4000]}...\n"
        except: continue
    return text_data

def get_news_summary():
    texto_final = ""
    print("Coletando notícias (Modo Ampliado)...")
    for categoria, urls in FEEDS.items():
        texto_final += f"\n--- {categoria} ---\n"
        for url in urls:
            try:
                feed = feedparser.parse(url)
                # Pega 4 notícias por fonte e bastante texto para análise
                for entry in feed.entries[:4]:
                    title = entry.title
                    content = entry.summary
                    if 'content' in entry:
                        content = entry.content[0].value
                    
                    summary = re.sub(r'<[^>]+>', '', content)[:2500]
                    published = entry.published if 'published' in entry else "Data Recente"
                    
                    source_name = "Fonte"
                    if 'source' in entry: source_name = entry.source.title
                    elif 'feed' in feed and 'title' in feed.feed: source_name = feed.feed.title
                    
                    texto_final += f"[{source_name} | {published}] {title}: {summary}\n"
            except: continue
            
    texto_final += get_custom_data()
    return texto_final

def clean_text_for_speech(text):
    text = text.replace("*", "")
    text = text.replace("#", "")
    text = re.sub(r'\[.*?\]', '', text) 
    text = re.sub(r'\(.*?\)', '', text) 
    text = re.sub(r'http\S+', '', text)
    text = text.replace("BRL", "reais")
    text = text.replace("USD", "dólares")
    return text

def make_script(news_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    model_name = 'gemini-pro'
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    model_name = m.name
                    break
    except: pass

    try:
        model = genai.GenerativeModel(model_name)
        data_hoje_extenso = get_data_ptbr()
        
        # --- PROMPT REAJUSTADO: MERCADO DA BOLA ATIVO MAS CONCISO ---
        prompt = f"""
        ATUE COMO: Um âncora de rádio sério, bem informado e analítico.
        OUVINTE: Yuri.
        DATA: {data_hoje_extenso}.
        OBJETIVO: Resumo completo e profundo (10 a 15 minutos).
        
        DIRETRIZES DE ESTILO:
        - Naturalidade total. Sem metalinguagem (não diga "agora o próximo bloco").
        - Profundidade analítica em Política e Economia.
        - Fale devagar e com clareza.
        
        ROTEIRO OBRIGATÓRIO:
        
        1. SAUDAÇÃO:
           - "Olá, bom dia Yuri! Hoje é {data_hoje_extenso}."
        
        2. CLIMA (GOIÂNIA):
           - Dados do INMET/Climatempo: Temperatura, chuva, alertas.
        
        3. ESPORTE (VILA NOVA & CRUZEIRO):
           - Fale de resultados, tabelas e jogos.
           - MERCADO DA BOLA: Pode falar sobre contratações e especulações fortes (quem chega, quem sai), mas seja OBJETIVO. Não delongue demais, apenas informe as movimentações relevantes e o impacto no time.
        
        4. GOIÁS E CIDADES:
           - Política estadual/municipal, obras e serviços.
        
        5. BRASIL (POLÍTICA, ECONOMIA, SOCIAL):
           - Use fontes como Valor, Nexo, IstoÉ. Explique as intrigas do poder e o cenário econômico.
           - Impacto na vida do cidadão.
        
        6. MUNDO (GEOPOLÍTICA GLOBAL):
           - Visão ampla (ONU, Al Jazeera, Le Monde). 
           - Ásia, África, Europa e Américas.
        
        7. CIÊNCIA, SAÚDE & CULTURA:
           - Inovações e descobertas relevantes.
        
        8. OPORTUNIDADES:
           - Concursos em destaque.
        
        9. DESPEDIDA:
           - "Espero que tenha gostado, Yuri. Um ótimo dia e até amanhã!"
        
        DADOS BRUTOS:
        {news_text}
        """
        
        response = model.generate_content(prompt)
        if response.text:
            return response.text
        return "Tivemos um problema técnico na geração do roteiro."
            
    except Exception as e:
        return f"Erro técnico: {str(e)[:100]}"

async def gen_audio(text, filename):
    clean_text = clean_text_for_speech(text)
    communicate = edge_tts.Communicate(clean_text, "pt-BR-AntonioNeural") 
    await communicate.save(filename)

def update_rss(audio_filename, title):
    rss_file = "feed.xml"
    audio_url = f"{BASE_URL}/{audio_filename}"
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    
    safe_title = escape(title).replace("&", "e") 
    
    rss_item = f"""
    <item>
      <title>{safe_title}</title>
      <description>Edição Completa para Yuri (Fontes Novas).</description>
      <enclosure url="{audio_url}" type="audio/mpeg" />
      <guid isPermaLink="true">{audio_url}</guid>
      <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
    </item>
    """
    
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Resumo Diario do Yuri</title>
    <description>Notícias aprofundadas.</description>
    <link>{BASE_URL}</link>
    <language>pt-br</language>
    <itunes:image href="https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/640px-Flag_of_Brazil.svg.png"/>
"""
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write(header + rss_item + "\n  </channel>\n</rss>")

if __name__ == "__main__":
    news = get_news_summary()
    if len(news) > 50:
        script = make_script(news)
        hoje = datetime.now(pytz.timezone('America/Sao_Paulo'))
        filename = f"podcast_{hoje.strftime('%Y%m%d')}.mp3"
        asyncio.run(gen_audio(script, filename))
        update_rss(filename, f"Resumo {hoje.strftime('%d/%m')}")
