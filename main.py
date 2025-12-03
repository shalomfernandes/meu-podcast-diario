import os
import feedparser
import google.generativeai as genai
import asyncio
import edge_tts
from datetime import datetime
import pytz
from xml.sax.saxutils import escape # Nova ferramenta de segurança

# --- CONFIGURAÇÕES DO USUÁRIO ---
GITHUB_USER = "yurileonardos"  # <--- COLOQUE SEU USUÁRIO GITHUB AQUI NOVAMENTE
REPO_NAME = "meu-podcast-diario"
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}"

# --- FONTES ---
FEEDS = {
    "LOCAL (GOIÂNIA E GOIÁS)": [
        "https://g1.globo.com/rss/g1/goias/",
        "https://www.jornalopcao.com.br/feed/",
        "https://www.maisgoias.com.br/feed/",
        "https://agenciabrasil.ebc.com.br/rss/regioes/centro-oeste"
    ],
    "BRASIL (POLÍTICA E ECONOMIA)": [
        "https://www.brasil247.com/feed",
        "https://cartacapital.com.br/feed/",
        "https://www.metropoles.com/feed",
        "https://agenciabrasil.ebc.com.br/rss/ultimas-noticias/feed.xml",
        "https://super.abril.com.br/feed/",
        "https://feeds.folha.uol.com.br/poder/rss091.xml"
    ],
    "DESTAQUES YOUTUBE": [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCO6j6cqBhi2TWVxfcn6t23w",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC6w8cK5C5QZJ9J9J9J9J9J9",
    ],
    "MUNDO": [
        "https://brasil.elpais.com/rss/elpais/america.xml",
        "https://www.bbc.com/portuguese/index.xml",
        "https://rss.dw.com/xml/rss-br-all",
    ]
}

def get_news_summary():
    texto_final = ""
    print("Coletando notícias...")
    for categoria, urls in FEEDS.items():
        texto_final += f"\n--- {categoria} ---\n"
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    title = entry.title
                    summary = entry.summary if 'summary' in entry else ""
                    summary = summary.replace("<p>", "").replace("</p>", "").replace("<strong>", "")[:300]
                    source_name = entry.get('source', {}).get('title', 'Fonte')
                    texto_final += f"Fonte: {source_name} | Título: {title} | Resumo: {summary}\n"
            except: continue
    return texto_final

def make_script(news_text):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    data_hoje = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d de %B')
    
    prompt = f"""
    Você é o âncora de um podcast jornalístico.
    Data: {data_hoje}.
    Resuma as notícias abaixo de forma completa e séria.
    Foco: Goiás, Brasil e Mundo.
    Não use caracteres especiais complexos.
    
    Notícias:
    {news_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return "Erro técnico. Voltamos amanhã."

async def gen_audio(text, filename):
    communicate = edge_tts.Communicate(text, "pt-BR-AntonioNeural") 
    await communicate.save(filename)

# --- A CORREÇÃO ESTÁ AQUI (Função Blindada) ---
def update_rss(audio_filename, title):
    rss_file = "feed.xml"
    audio_url = f"{BASE_URL}/{audio_filename}"
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    
    # Limpa caracteres perigosos do título
    safe_title = escape(title).replace("&", "e") 
    
    rss_item = f"""
    <item>
      <title>{safe_title}</title>
      <description>Notícias do dia.</description>
      <enclosure url="{audio_url}" type="audio/mpeg" />
      <guid isPermaLink="true">{audio_url}</guid>
      <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
    </item>
    """
    
    # Cabeçalho corrigido: "Goiás e Brasil" em vez de "&"
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Goias e Brasil Diario</title>
    <description>Resumo diário.</description>
    <link>{BASE_URL}</link>
    <language>pt-br</language>
    <itunes:image href="https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/640px-Flag_of_Brazil.svg.png"/>
"""
    
    if not os.path.exists(rss_file):
        with open(rss_file, 'w', encoding='utf-8') as f:
            f.write(header + rss_item + "\n  </channel>\n</rss>")
    else:
        with open(rss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Se o arquivo antigo estiver corrompido ou com erro, recria do zero
        if "xmlParseEntityRef" in content or "& " in content: 
             with open(rss_file, 'w', encoding='utf-8') as f:
                f.write(header + rss_item + "\n  </channel>\n</rss>")
        else:
            if "<itunes:image" in content:
                pos = content.find("/>", content.find("<itunes:image")) + 2
                new_content = content[:pos] + rss_item + content[pos:]
                with open(rss_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

if __name__ == "__main__":
    news = get_news_summary()
    if len(news) > 100:
        script = make_script(news)
        hoje = datetime.now(pytz.timezone('America/Sao_Paulo'))
        filename = f"podcast_{hoje.strftime('%Y%m%d')}.mp3"
        asyncio.run(gen_audio(script, filename))
        update_rss(filename, f"Edicao {hoje.strftime('%d/%m')}")
