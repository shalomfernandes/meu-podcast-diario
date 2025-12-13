# Meu Podcast Diário

Sistema automatizado que consolida notícias de múltiplas fontes RSS e gera um podcast em áudio diariamente usando IA.

## 🎯 Funcionalidades

- **Coleta automática de notícias** de diversas fontes (G1, Nexo, Valor, ONU, BBC, etc.)
- **Geração de roteiro** usando Google Gemini AI
- **Síntese de voz** usando Microsoft Edge TTS (voz pt-BR-AntonioNeural)
- **Feed RSS** atualizado automaticamente para distribuição no Spotify
- **Execução diária** via GitHub Actions

## 📋 Pré-requisitos

- Python 3.11+
- Conta no GitHub
- API Key do Google Gemini
- Repositório GitHub configurado com GitHub Pages

## 🚀 Configuração

### 1. Configurar Secrets no GitHub

1. Vá para o seu repositório no GitHub
2. Clique em **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione o secret:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Sua chave da API do Google Gemini

### 2. Configurar GitHub Pages

1. Vá para **Settings** → **Pages**
2. Em **Source**, selecione **Deploy from a branch**
3. Escolha a branch `main` e pasta `/ (root)`
4. Salve

### 3. Ajustar Configurações no Código

Edite o arquivo `main.py` e ajuste as variáveis:

```python
GITHUB_USER = "seu-usuario-github"
REPO_NAME = "meu-podcast-diario"
```

### 4. Personalizar Fontes de Notícias

Edite o dicionário `FEEDS` em `main.py` para adicionar ou remover fontes RSS conforme necessário.

## 📅 Agendamento

O workflow está configurado para executar diariamente às **06:50 (horário de Brasília)**.

Para executar manualmente:
1. Vá para **Actions** no seu repositório
2. Selecione o workflow **Podcast Diario**
3. Clique em **Run workflow**

## 📦 Estrutura do Projeto

```
meu-podcast-diario/
├── .github/
│   └── workflows/
│       └── daily.yml          # Workflow do GitHub Actions
├── main.py                     # Script principal
├── requirements.txt            # Dependências Python
├── feed.xml                    # Feed RSS do podcast
└── podcast_YYYYMMDD.mp3        # Arquivos de áudio gerados
```

## 🔧 Dependências

- `google-generativeai` - API do Google Gemini
- `feedparser` - Parser de feeds RSS
- `edge-tts` - Síntese de voz
- `pytz` - Fuso horário
- `aiohttp` - Requisições assíncronas

## 📝 Notas

- Os arquivos de áudio são gerados no formato MP3
- O feed RSS mantém os últimos 10 episódios
- O workflow faz commit automático dos novos episódios
- Certifique-se de que o repositório está público ou que o GitHub Pages está configurado corretamente

## 🎧 Como Usar no Spotify

1. Certifique-se de que o `feed.xml` está acessível via GitHub Pages
2. Acesse o [Spotify for Podcasters](https://podcasters.spotify.com/)
3. Adicione seu feed RSS: `https://seu-usuario.github.io/meu-podcast-diario/feed.xml`
4. Siga as instruções para publicar no Spotify

## ⚠️ Troubleshooting

- **Erro na geração do áudio**: Verifique se o `edge-tts` está instalado corretamente
- **Feed RSS não atualiza**: Verifique as permissões do workflow (deve ter `contents: write`)
- **API Key inválida**: Verifique se o secret `GEMINI_API_KEY` está configurado corretamente