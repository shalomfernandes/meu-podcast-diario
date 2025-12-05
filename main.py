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

# --- 1. FONTES CONVERTIDAS PARA RSS (ROBÔ) ---
FEEDS = {
    "GOIÁS E GOIÂNIA": [
        "https://g1.globo.com/rss/g1/goias/",
        "https://www.jornalopcao.com.br/feed/",
        "https://www.maisgoias.com.br/feed/",
        "https://opopular.com.br/rss",
        "https://www.dm.com.br/feed",
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
        "https://rss.uol.com.br/feed/noticias.xml",
        "https://feeds.folha.uol.com.br/poder/rss091.xml",
        "https://www.estadao.com.br/rss/politica",
        "https://www.cnnbrasil.com.br/feed/",
        "https://www.brasil247.com/feed",
        "https://cartacapital.com.br/feed/",
        "https://agenciabrasil.ebc.com.br/rss/ultimas-noticias/feed.xml",
        "https://www.camara.leg.br/noticias/rss/ultimas-noticias",
        "https://www12.senado.leg.br/noticias/feed/todas/rss",
        "https://iclnoticias.com.br/feed/",
        "https://veja.abril.com.br/feed/",
        "https://exame.com/feed/",
        "https://exame.com/negocios/feed/",
        "https://valor.globo.com/rss/",
        "https://www.seudinheiro.com/feed/",
        "https://piaui.folha.uol.com.br/feed/",
        "https://www.infomoney.com.br/feed/",
        "https://www.correiobraziliense.com.br/rss/noticia/brasil.xml",
        "https://www.gazetadopovo.com.br/feed/",
        "https://www.metropoles.com/feed",
        "https://www.em.com.br/rss/noticia/nacional/"
    ],
    "MUNDO (Geopolítica Global)": [
        "https://brasil.elpais.com/rss/elpais/america.xml",      
        "https://www.bbc.com/portuguese/index.xml",              
        "https://rss.dw.com/xml/rss-br-all",                     
        "https://news.un.org/feed/subscribe/pt/news/all/rss.xml", 
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 
        "https://www.theguardian.com/world/rss",
        "https://www.clarin.com/rss/lo-ultimo/",
        "https://pt.euronews.com/rss?format=xml",
        "https://forbes.com.br/feed/",
        "https://www.ft.com/rss/home"
    ],
    "CIÊNCIA, TECNOLOGIA E CULTURA": [
        "https://super.abril.com.br/feed/",
        "https://gizmodo.uol.com.br/feed/",
        "https://www.nature.com/nature.rss",
        "https://quatrocincoum.com.br/feed/",
        "https://www.abc.org.br/feed/",
        "https://www.gov.br/cultura/pt-br/rss.xml",
        "https://feeds.folha.uol.com.br/ilustrada/rss091.xml",
        "https://saude.abril.com.br/feed/"
    ],
    "YOUTUBE (Canais Específicos)": [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCO6j6cqBhi2TWVxfcn6t23w", # Desmascarando
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC6w8cK5C5QZJ9J9J9J9J9J9", # ICL Canal
        "https://www.youtube.com/feeds/videos.xml?playlist_id=PL5DFl3pSRD_9TJB8i1IHZfl63rfF0DrcH" # ICL Playlist
    ]
}

# --- 2. LINKS ESPECIAIS (CLIMA) ---
WEATHER_URLS = [
    "https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/88/goiania-go",
    "https://g1.globo.com/previsao-do-tempo/go/goiania.ghtml"
]

# --- 3. FERRAMENTAS ---
def get_data_ptbr():
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
    meses = ['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    return f"{now.day} de {meses[now.month]}, uma {dias[now.weekday()]}"

def get_weather_data():
    text_data = "\n--- PREVISÃO DO TEMPO EM GOIÂNIA (Dados Brutos) ---\n"
    print("Consultando sites de clima...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in WEATHER_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                clean = re.sub(r'<[^>]+>', ' ', html)
                clean = re.sub(r'\s+', ' ', clean)
                text_data += f"Fonte ({url}): {clean[:1000]}...\n"
        except: continue
    return text_data

def get_news_summary():
    texto_final = ""
    print("Coletando notícias RSS...")
    for categoria, urls in FEEDS.items():
        texto_final += f"\n--- {categoria} ---\n"
        for url in urls:
            try:
                feed = feedparser.parse(url)
                # Pega 2 notícias de cada para não estourar o tamanho
                for entry in feed.entries[:2]:
                    title = entry.title
                    summary = entry.summary if 'summary' in entry else ""
                    summary = re.sub(r'<[^>]+>', '', summary)[:200]
                    
                    source_name = "Fonte"
                    if 'source' in entry: source_name = entry.source.title
                    elif 'feed' in feed and 'title' in feed.feed: source_name = feed.feed.title
                    
                    texto_final += f"[{source_name}] {title}: {summary}\n"
            except: continue
            
    texto_final += get_weather_data()
    return texto_final

def clean_text_for_speech(text):
    text = text.replace("*", "")
    text = text.replace("#", "")
    text = re.sub(r'\[.*?\]', '', text)
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
        
        prompt = f"""
        Você é o âncora pessoal do Yuri. 
        Data de hoje: {data_hoje_extenso}.
        
        1. SAUDAÇÃO OBRIGATÓRIA: "Olá, bom dia Yuri! Hoje é {data_hoje_extenso}."
        
        2. FILTRO NEGATIVO (O QUE NÃO FALAR):
           - PROIBIDO falar de acidentes de trânsito, crimes comuns, roubos, assassinatos isolados ou tragédias irrelevantes.
           - Se a notícia for "acidente na ponte", IGNORE.
           - Foque no MACRO: Políticas Públicas, Economia, Decisões de Governo, Inovação.
        
        3. ROTEIRO OBRIGATÓRIO:
           
           - CLIMA EM GOIÂNIA:
             * Procure no texto bruto os dados do Climatempo/G1. Diga a temperatura máxima/mínima e se vai chover.
           
           - GOIÂNIA & GOIÁS:
             * Políticas públicas (Prefeitura/Estado), obras e sociedade.
           
           - ESPORTE (VILA NOVA & CRUZEIRO):
             * Fale do Tigrão (Vila) e da Raposa (Cruzeiro).
             * Se não tiver jogo, fale dos bastidores ou contratações.
           
           - BRASIL & MUNDO:
             * Resumo sério de política, economia e geopolítica.
             * Cruze as informações das fontes (ex: NY Times com BBC).
           
           - OPORTUNIDADES & CULTURA:
             * Concursos públicos abertos.
             * Inovação e Ciência.
        
        4. DESPEDIDA: "Espero que tenha gostado. Um ótimo dia e até amanhã!"
        
        DADOS BRUTOS PARA ANÁLISE:
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
      <description>Resumo diário completo para Yuri.</description>
      <enclosure url="{audio_url}" type="audio/mpeg" />
      <guid isPermaLink="true">{audio_url}</guid>
      <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
    </item>
    """
    
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Resumo Diario do Yuri</title>
    <description>Notícias personalizadas.</description>
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
