import os
from dotenv import load_dotenv
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
import docx2txt
from openai import OpenAI

# Para OCR
from pdf2image import convert_from_path
import pytesseract

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGChatbot:
    def __init__(self, system_prompt: str):
        self.client = Client(Settings())
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        self.collection = None
        self.documents = []
        self.system_prompt = system_prompt
        self.tokens_used = 0
        self.history = []

    # Splitter simple
    def split_text(self, text, chunk_size=1000, overlap=200):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    # OCR para PDFs de imagen
    def ocr_pdf(self, filepath):
        pages = convert_from_path(filepath)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, lang="spa") + "\n"
        return text

    # Cargar documento (PDF o Word)
    def load_document(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        texts = []

        if ext == ".pdf":
            reader = PdfReader(filepath)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    texts.append(page_text)
            
            # Si no se extrajo texto, hacer OCR
            if not texts:
                ocr_text = self.ocr_pdf(filepath)
                if ocr_text.strip():
                    texts = [ocr_text]
                else:
                    raise ValueError("No se pudo extraer texto del PDF ni con OCR.")

        elif ext == ".docx":
            text = docx2txt.process(filepath)
            if text.strip():
                texts.append(text)
            else:
                raise ValueError("El archivo DOCX está vacío.")
        else:
            raise ValueError("Formato no soportado. Usa PDF o DOCX.")

        # Dividir en chunks
        self.documents = []
        for t in texts:
            self.documents.extend(self.split_text(t))

        # Crear colección Chroma
        self.collection = self.client.get_or_create_collection(
            name="legal_docs",
            embedding_function=self.embedding_fn
        )

        # Insertar documentos en Chroma
        for i, doc in enumerate(self.documents):
            self.collection.add(
                documents=[doc],
                metadatas=[{"id": str(i)}],
                ids=[str(i)]
            )

    # Preguntar al modelo con idioma opcional
    def ask(self, query, language_instruction=""):
        if self.collection is None:
            return "Por favor, carga primero un documento.", 0

        # Recuperar contexto relevante
        results = self.collection.query(
            query_texts=[query],
            n_results=3
        )
        context = "\n".join(results['documents'][0])

        # Construir mensajes con memoria conversacional
        system_content = self.system_prompt
        if language_instruction:
            system_content += f"\n{language_instruction}"

        messages = [{"role": "system", "content": system_content}]
        for q, a in self.history:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})

        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"})

        # Llamada a OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2
        )

        answer = response.choices[0].message.content
        usage = response.usage.total_tokens
        self.tokens_used += usage

        # Guardar en memoria conversacional
        self.history.append((query, answer))

        return answer, self.tokens_used



