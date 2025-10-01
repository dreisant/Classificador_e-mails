# EmAIl Classifier - Classificador Inteligente de E-mails

Este projeto é uma aplicação web desenvolvida como solução para o case do processo seletivo da AutoU - Desenvolvimento. A aplicação utiliza Inteligência Artificial para classificar e-mails como "Produtivos" ou "Improdutivos" e sugerir respostas adequadas. Sendo assim uma solução interessante e eficiente para empresas que lidam com um alto fluxo de emails diariamente.

## ✨ Funcionalidades Principais

- Upload de e-mails em formato `.txt` ou `.pdf`.
- Classificação de e-mails usando um sistema híbrido com IA (via Hugging Face) e regras de negócio (sistema de veto) para maior precisão.
- Geração de respostas automáticas com base na classificação.
- Interface web moderna e intuitiva.

## 🚀 Tecnologias Utilizadas

- **Backend:** Python, Flask
- **Inteligência Artificial:** Hugging Face Inference API (modelo `valhalla/distilbart-mnli-12-3`)
- **Frontend:** HTML5, CSS3 (Flexbox), CSS, JavaScript
- **Bibliotecas Python:** PyPDF2, python-dotenv, requests

## ⚙️ Como Executar Localmente

1. Clone este repositório:
   `git clone [URL_DO_SEU_REPO]`
2. Crie e ative um ambiente virtual:
   `python -m venv venv`
   `.\venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (macOS/Linux)
3. Instale as dependências:
   `pip install -r requirements.txt`
4. Crie um arquivo `.env` na raiz do projeto e adicione sua chave da API do Hugging Face:
   `HUGGING_FACE_TOKEN="hf_sua_chave_aqui"`
5. Execute a aplicação:
   `python app.py`
6. Acesse `http://127.0.0.1:5000` no seu navegador.

## 📊 Dados de Exemplo

Na pasta `/exemplos`, você encontrará arquivos `.txt` e `.pdf` prontos para teste, cobrindo diferentes cenários de classificação.
Caso queira gerar um arquivo com outras mensagens para teste, o formato ideal segue dessa forma:
- **Para emails que vem com assunto** 
Assunto:  
Mensagem:

- **Para emails que vem só a mensagem**
Mensagem:
