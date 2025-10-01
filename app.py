import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import PyPDF2
import re
import requests

PRODUTIVO_KEYWORDS = [
    "preciso", "solicito", "atualiza", "atualização", "atualizacao",
    "status", "erro", "problema", "suporte", "consulta", "reembolso", "documento",
    "relatório", "relatorio", "revisão", "revisao", "contrato", "assinatura", 
    "cadastro", "anexo", "segue", "encaminhando", "verificar"
]

IMPRODUTIVO_KEYWORDS = [
    "feliz natal", "feliz ano novo", "próspero ano", "parabéns", "parabenizar",
    "obrigado", "obrigada", "agradeço", "grato", "grata", "valeu",
    "convite", "convidados", "café da manhã", "happy hour", "artigo"
]

load_dotenv()

app = Flask(__name__, template_folder="templates")

# ======= Config Hugging Face (opcional) =======
HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")


import pdfplumber


def allowed_file(filename):
    """Retorna True se extensão for txt ou pdf"""
    if not filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ("txt", "pdf")

def extract_text(file_storage):
    """
    Recebe um FileStorage (file) do Flask e retorna o texto extraído.
    Suporta .txt (utf-8) e .pdf (PyPDF2).
    """
    filename = file_storage.filename.lower()
    if filename.endswith(".txt"):
        # lê bytes e decodifica como utf-8
        raw = file_storage.read()
        try:
            return raw.decode("utf-8")
        except Exception:
            # fallback para latin-1 caso venha assim
            return raw.decode("latin-1", errors="ignore")
    elif filename.endswith(".pdf"):
        
        try:
            reader = PyPDF2.PdfReader(file_storage)
            pages = []
            for p in reader.pages:
                text = p.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except Exception as e:
            print("Erro extraindo PDF:", e)
            return ""
    else:
        return ""


def parse_emails(text):
    """
    Parser inteligente para PDFs com e sem Assunto.
    """
    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    has_assunto = bool(re.search(r'(?i)assunto:', text))

    emails = []

    if has_assunto:
        # lógica para PDFs com Assunto/Mensagem
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        temp_email = {"assunto": None, "mensagem": None}
        collecting_msg = False

        for line in lines:
            if re.match(r'(?i)^assunto:', line):
                if temp_email["assunto"] or temp_email["mensagem"]:
                    emails.append(temp_email)
                    temp_email = {"assunto": None, "mensagem": None}
                temp_email["assunto"] = re.sub(r'(?i)^assunto:\s*', '', line).strip()
                collecting_msg = False
            elif re.match(r'(?i)^mensagem:', line):
                temp_email["mensagem"] = re.sub(r'(?i)^mensagem:\s*', '', line).strip()
                collecting_msg = True
            else:
                if collecting_msg:
                    temp_email["mensagem"] = (temp_email["mensagem"] + "\n" + line).strip() if temp_email["mensagem"] else line
                else:
                   
                    if not temp_email["mensagem"]:
                        temp_email["mensagem"] = line

        if temp_email["assunto"] or temp_email["mensagem"]:
            emails.append(temp_email)

    else:
        # PDFs sem Assunto: cada "Mensagem:" inicia um email
        # força quebra antes de cada "Mensagem:"
        text = re.sub(r'(?i)(?<!\n)(Mensagem:)', r'\n\1', text)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        temp_email = None
        for line in lines:
            if re.match(r'(?i)^mensagem:', line):
                if temp_email:
                    emails.append(temp_email)
                temp_email = {"assunto": None, "mensagem": re.sub(r'(?i)^mensagem:\s*', '', line).strip()}
            else:
                if temp_email:
                    temp_email["mensagem"] += "\n" + line
        if temp_email:
            emails.append(temp_email)

    return emails


# ======= Classificação (fallback) =======
def classificar_email(texto_base):
    """
    Recebe string (assunto+mensagem ou só mensagem) e devolve:
    (classificacao_str, resposta_texto, css_class)
    """
    if not texto_base:
        return "Indefinido", "Recebemos sua mensagem. Nossa equipe avalia.", "indefinido"

    t = texto_base.lower()

    # palavras-chave produtivo
    produtivo_kw = [
        "preciso", "solicito", "gostaria", "atualiza", "atualização", "atualizacao",
        "status", "erro", "problema", "suporte", "consulta", "reembolso", "documento",
        "relatório", "relatorio", "revisão","podem", "revisao", "contrato", "assinatura", "cadastro"
    ]
    # palavras-chave improdutivo
    improdutivo_kw = [
        "feliz natal", "parabéns", "parabens", "obrigado", "obrigada", "valeu",
        "convite", "café", "cafe", "parabéns", "compartilhando", "bom dia", "boa tarde"
    ]

    for kw in produtivo_kw:
        if kw in t:
            return "Produtivo", "Sua solicitação foi registrada e está em análise. Em breve retornaremos com novidades.", "produtivo"

    for kw in improdutivo_kw:
        if kw in t:
            return "Improdutivo", "Agradecemos sua mensagem! Não é necessária nenhuma ação adicional.", "improdutivo"

    return "Indefinido", "Recebemos sua mensagem. Nossa equipe vai avaliar.", "indefinido"

# ======= Função que tenta usar HuggingFace =======
def try_huggingface_classify(texto):
    """
    Tenta usar a API do Hugging Face para classificar.
    Retorna (mode, classificacao, resposta, css_class) ou None se falhar.
    """
    if not HF_TOKEN:
        return None

    API_URL = "https://api-inference.huggingface.co/models/valhalla/distilbart-mnli-12-3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    payload = {
        "inputs": texto,
        "parameters": {"candidate_labels": ["ação requerida", "agradecimento ou felicitação"]},
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() 
        output = response.json()

        classificacao_raw = output['labels'][0]

        if classificacao_raw == "ação requerida":
            classificacao = "Produtivo"
            resposta_sugerida = "Sua solicitação foi registrada e está em análise. Em breve retornaremos com novidades."
            css = "produtivo"
        else: 
            classificacao = "Improdutivo"
            resposta_sugerida = "Agradecemos sua mensagem! Não é necessária nenhuma ação adicional."
            css = "improdutivo"

        return ("huggingface", classificacao, resposta_sugerida, css)

    except Exception as e:
        print(f"Hugging Face erro: {e}")
        return None

# ======= Rotas =======
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "mode": "openai" if openai_client else "fallback"})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    texto = data.get("text", "")

    if HF_TOKEN:  #primeiro tenta Hugging Face
        out = try_huggingface_classify(texto)
        if out:
            mode, classificacao, resposta, css = out
            return jsonify({"mode": mode, "emails": [{
                "assunto": None, "mensagem": texto, "classificacao": classificacao, "resposta": resposta, "css_class": css
            }]})

    # Fallback (continua igual)
    tipo, resposta, css = classificar_email(texto)
    return jsonify({"mode": "fallback", "emails": [{
        "assunto": None, "mensagem": texto, "classificacao": tipo, "resposta": resposta, "css_class": css
    }]})

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files: return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files["file"]
    if not allowed_file(file.filename): return jsonify({"error": "Formato não suportado"}), 400
    text = extract_text(file)
    if not text: return jsonify({"error": "Não foi possível extrair texto."}), 400

    emails = parse_emails(text)
    resultados = []

    for e in emails:
        assunto = e.get("assunto") or ""
        mensagem = e.get("mensagem") or ""
        base = (assunto + " " + mensagem).strip()
        base_lower = base.lower()

        # PASSO 1: DEIXAR A IA FAZER A CLASSIFICAÇÃO INICIAL
        classificacao, resposta, css = None, None, None

        if HF_TOKEN:
            out = try_huggingface_classify(base)
            if out:
                mode, classificacao, resposta, css = out

        # Se a IA falhou, usar o fallback local como classificação inicial
        if not classificacao:
            classificacao, resposta, css = classificar_email(base)

        # PASSO 2: APLICAR NOSSAS REGRAS DE CORREÇÃO (SISTEMA DE VETO)
        tem_kw_produtivo = any(kw in base_lower for kw in PRODUTIVO_KEYWORDS)
        tem_kw_improdutivo = any(kw in base_lower for kw in IMPRODUTIVO_KEYWORDS)

        # Regra 1: Veto de Improdutividade
        # Se a IA disse Produtivo, mas o e-mail parece só um agradecimento, corrigimos.
        if classificacao == "Produtivo" and tem_kw_improdutivo and not tem_kw_produtivo:
            classificacao = "Improdutivo"
            resposta = "Agradecemos sua mensagem! Não é necessária nenhuma ação adicional."
            css = "improdutivo"

        # Regra 2: Veto de Produtividade
        # Se a IA disse Improdutivo, mas tem uma tarefa clara, corrigimos.
        if classificacao == "Improdutivo" and tem_kw_produtivo:
            classificacao = "Produtivo"
            resposta = "Sua solicitação foi registrada e está em análise. Em breve retornaremos com novidades."
            css = "produtivo"

        resultados.append({
            "assunto": assunto,
            "mensagem": mensagem,
            "classificacao": classificacao,
            "resposta": resposta,
            "css_class": css
        })

    response_data = {"mode": "huggingface_veto_system", "emails": resultados}
    response = app.response_class(
        response=json.dumps(response_data, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )
    return response

if __name__ == "__main__":
    app.run(debug=True)
