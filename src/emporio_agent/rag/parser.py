import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pypdf import PdfReader

from emporio_agent.config import settings

logger = logging.getLogger(__name__)


class PolicyChunk(BaseModel):
    chunk_id: str
    section_number: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


# Authoritative sections of the Empório da Música Customer Service Policy Manual
POLICY_SECTIONS = [
    {
        "sec": "1",
        "title": "Sobre a Empório da Música",
        "tags": ["sobre", "historia", "missao", "escopo", "acessorios", "instrumentos"],
    },
    {
        "sec": "1.1",
        "title": "Missão",
        "tags": ["missao", "democratizar", "centro-oeste", "musica"],
    },
    {
        "sec": "1.2",
        "title": "Dados da Empresa",
        "tags": ["dados", "empresa", "cnpj", "endereco", "rua 14 de maio", "campo grande", "telefone", "whatsapp", "email", "fundacao"],
    },
    {
        "sec": "2",
        "title": "Horário de Funcionamento",
        "tags": ["horario", "funcionamento", "abertura", "atendimento", "sabado", "domingo", "feriado", "expediente", "semana"],
    },
    {
        "sec": "3",
        "title": "Formas de Pagamento",
        "tags": ["pagamento", "formas", "pix", "desconto 5%", "cartao de debito", "cartao de credito", "boleto", "parcelas"],
    },
    {
        "sec": "3.1",
        "title": "Regras de Parcelamento",
        "tags": ["parcelamento", "sem juros", "parcela minima", "12x", "combinacao pix cartao"],
    },
    {
        "sec": "4",
        "title": "Política de Trocas e Devoluções",
        "tags": ["troca", "devolucao", "regras", "cdc", "codigo de defesa do consumidor"],
    },
    {
        "sec": "4.1",
        "title": "Direito de Arrependimento (Compras Online)",
        "tags": ["arrependimento", "devolucao", "compras online", "7 dias", "reembolso", "estorno", "frete gratis devolucao"],
    },
    {
        "sec": "4.2",
        "title": "Trocas por Defeito",
        "tags": ["trocas por defeito", "fabricacao", "30 dias", "garantia fabricante", "mau uso"],
    },
    {
        "sec": "4.3",
        "title": "Trocas por Preferência",
        "tags": ["trocas por preferencia", "cor", "modelo", "tamanho", "7 dias", "embalagem original"],
    },
    {
        "sec": "4.4",
        "title": "Itens Não Elegíveis para Troca",
        "tags": ["itens nao elegiveis", "personalizacao", "sob encomenda", "liquidacao", "venda final", "boquilhas"],
    },
    {
        "sec": "5",
        "title": "Política de Frete e Entregas",
        "tags": ["frete", "entrega", "envio", "prazos", "transporte"],
    },
    {
        "sec": "5.1",
        "title": "Entregas na Região Metropolitana de Campo Grande",
        "tags": ["campo grande", "metropolitana", "motoboy", "frete gratis", "500 reais", "taxa fixa 35 reais", "1 a 3 dias"],
    },
    {
        "sec": "5.2",
        "title": "Entregas para Outras Cidades",
        "tags": ["outras cidades", "correios", "pac", "sedex", "jadlog", "rastreamento", "seguro"],
    },
    {
        "sec": "5.3",
        "title": "Código de Rastreamento",
        "tags": ["codigo de rastreamento", "rastreio", "formato br", "alfanumerico", "correios", "jadlog"],
    },
    {
        "sec": "6",
        "title": "Promoções e Descontos",
        "tags": ["promocoes", "descontos", "ofertas"],
    },
    {
        "sec": "6.1",
        "title": "Tipos de Promoção",
        "tags": ["aniversario", "black friday", "volta as aulas", "queima de estoque", "semana do musico"],
    },
    {
        "sec": "6.2",
        "title": "Regras de Promoções",
        "tags": ["regras promocoes", "nao cumulativo", "desconto pix", "sem reserva", "transparencia"],
    },
    {
        "sec": "7",
        "title": "Atendimento via WhatsApp",
        "tags": ["atendimento", "whatsapp", "canal", "assistente virtual"],
    },
    {
        "sec": "7.1",
        "title": "Diretrizes de Atendimento",
        "tags": ["tom de voz", "amigo que entende de musica", "acolhido", "nao vender acessorios", "redirecionar cordas palhetas"],
    },
    {
        "sec": "7.2",
        "title": "Fluxo de Atendimento Padrão",
        "tags": ["fluxo", "saudacao", "entendimento", "consulta", "resposta", "fechamento"],
    },
    {
        "sec": "7.3",
        "title": "Situações Especiais",
        "tags": ["situacoes especiais", "fora de estoque", "descontinuado", "promocao expirada", "reclamacao"],
    },
    {
        "sec": "8",
        "title": "Garantia",
        "tags": ["garantia", "prazos", "cobertura"],
    },
    {
        "sec": "8.1",
        "title": "Garantia Legal",
        "tags": ["garantia legal", "cdc", "90 dias", "defeito de fabricacao"],
    },
    {
        "sec": "8.2",
        "title": "Garantia do Fabricante",
        "tags": ["garantia do fabricante", "6 meses a 2 anos", "certificado"],
    },
    {
        "sec": "8.3",
        "title": "O que Não Cobre a Garantia",
        "tags": ["nao cobre", "desgaste natural", "trastes", "cordas", "feltros", "palhetas", "mau uso", "queda"],
    },
    {
        "sec": "9",
        "title": "Privacidade e Proteção de Dados",
        "tags": ["privacidade", "lgpd", "dados pessoais", "exclusao"],
    },
    {
        "sec": "10",
        "title": "Disposições Finais",
        "tags": ["disposicoes finais", "duvidas", "gerencia", "documento interno"],
    },
]


class PolicyParser:
    """Extracts and chunks store policy document."""

    def __init__(self, pdf_path: Optional[Path | str] = None):
        self.pdf_path = Path(pdf_path) if pdf_path else settings.POLICY_PDF_PATH

    def extract_full_text(self) -> str:
        """Extract all text across pages and normalize whitespace."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Policy PDF file not found at: {self.pdf_path}")

        reader = PdfReader(str(self.pdf_path))
        full_pages = []
        for page in reader.pages:
            raw = page.extract_text() or ""
            t = re.sub(r"[\r\n]+", " ", raw)
            t = re.sub(r"\s+", " ", t).strip()
            t = re.sub(r"Empório da Música Manual de Políticas e Procedimentos", "", t)
            t = re.sub(r"Página\s+\d+", "", t)
            full_pages.append(t)
        return " ".join(full_pages)

    def parse_chunks(self) -> List[PolicyChunk]:
        """Parse text into sections matching the store policy catalog."""
        full_text = self.extract_full_text()
        chunks: List[PolicyChunk] = []

        # Find position of each section title in the full text
        found_positions = []
        for sec_info in POLICY_SECTIONS:
            sec_num = sec_info["sec"]
            title = sec_info["title"]
            # Look for "X. Title" or "X.Y Title"
            pattern = re.compile(rf"\b{re.escape(sec_num)}\.\s+{re.escape(title)}", re.IGNORECASE)
            match = pattern.search(full_text)
            if match:
                found_positions.append((match.start(), match.end(), sec_info))

        found_positions.sort(key=lambda x: x[0])

        for i, (start, end_header, sec_info) in enumerate(found_positions):
            next_start = found_positions[i + 1][0] if i + 1 < len(found_positions) else len(full_text)
            body = full_text[end_header:next_start].strip()

            chunks.append(
                PolicyChunk(
                    chunk_id=f"sec_{sec_info['sec'].replace('.', '_')}",
                    section_number=sec_info["sec"],
                    title=f"{sec_info['sec']}. {sec_info['title']}",
                    content=body,
                    tags=sec_info["tags"],
                )
            )

        return chunks
