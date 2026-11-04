import logging
import re
from typing import List, Optional
from rank_bm25 import BM25Okapi

from emporio_agent.rag.parser import PolicyChunk, PolicyParser

logger = logging.getLogger(__name__)

PORTUGUESE_STOPWORDS = {
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as", "ate", "com",
    "como", "da", "das", "de", "dela", "delas", "dele", "deles", "depois", "do", "dos", "e",
    "ela", "elas", "ele", "eles", "em", "entre", "era", "eram", "eramos", "essa", "essas",
    "esse", "esses", "esta", "estamos", "estas", "estava", "estavam", "este", "estes", "estou",
    "eu", "foi", "fomos", "foram", "ha", "isso", "isto", "ja", "lhe", "lhes", "mais", "mas",
    "me", "mesmo", "meu", "meus", "minha", "minhas", "muito", "na", "nao", "nas", "nem",
    "no", "nos", "nossa", "nossas", "nosso", "nossos", "num", "numa", "o", "os", "ou",
    "para", "pela", "pelas", "pelo", "pelos", "por", "qual", "quando", "que", "quem", "se",
    "seja", "sem", "ser", "seu", "seus", "so", "sua", "suas", "tambem", "te", "tem",
    "temos", "tenho", "teve", "ti", "tido", "tinha", "tinham", "toda", "todas", "todo",
    "todos", "tu", "tua", "tuas", "um", "uma", "voces", "vos", "pra", "pro"
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text for BM25 retrieval."""
    text = text.lower()
    # Normalize accents for common search terms
    replacements = (
        ("á", "a"), ("à", "a"), ("ã", "a"), ("â", "a"),
        ("é", "e"), ("ê", "e"),
        ("í", "i"),
        ("ó", "o"), ("õ", "o"), ("ô", "o"),
        ("ú", "u"),
        ("ç", "c"),
    )
    for orig, rep in replacements:
        text = text.replace(orig, rep)

    tokens = re.findall(r"\b\w{2,}\b", text)
    return [t for t in tokens if t not in PORTUGUESE_STOPWORDS]


class PolicyRetriever:
    """Retrieves relevant policy sections using BM25 and semantic metadata matching."""

    def __init__(self, parser: Optional[PolicyParser] = None):
        self.parser = parser or PolicyParser()
        self.chunks: List[PolicyChunk] = []
        self._bm25: Optional[BM25Okapi] = None
        self._load_and_index()

    def _load_and_index(self) -> None:
        try:
            self.chunks = self.parser.parse_chunks()
            if not self.chunks:
                logger.warning("No chunks parsed from policy PDF. Using fallback chunks.")
                self._load_fallback_chunks()
        except Exception as e:
            logger.error(f"Failed to parse policy PDF: {e}. Using fallback knowledge.")
            self._load_fallback_chunks()

        corpus = [
            tokenize(f"{c.section_number} {c.title} {' '.join(c.tags)} {c.content}")
            for c in self.chunks
        ]
        self._bm25 = BM25Okapi(corpus)
        logger.info(f"Policy retriever indexed {len(self.chunks)} chunks.")

    def _load_fallback_chunks(self) -> None:
        """Embedded essential policy sections in case PDF is moved or unreadable."""
        self.chunks = [
            PolicyChunk(
                chunk_id="sec_1",
                section_number="1",
                title="Sobre a Empório da Música e Dados da Empresa",
                content=(
                    "Fundada em 2008 em Campo Grande/MS. Razão Social: Empório da Música Instrumentos Musicais Ltda. "
                    "CNPJ: 12.345.678/0001-90. Endereço: Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333. "
                    "Telefone / WhatsApp: (67) 3341-4444. E-mail: contato@emporiodamusica.com.br. "
                    "IMPORTANTE: Trabalhamos EXCLUSIVAMENTE com instrumentos musicais. NÃO comercializamos acessórios "
                    "como cordas, palhetas, cabos, cases, pedais ou amplificadores."
                ),
                tags=["sobre", "endereco", "contato", "telefone", "whatsapp", "cnpj", "acessorios", "escopo"],
            ),
            PolicyChunk(
                chunk_id="sec_2",
                section_number="2",
                title="Horário de Funcionamento",
                content=(
                    "Atendimento presencial e WhatsApp: Segunda a Sexta-feira das 09:00 às 18:00. "
                    "Sábado das 09:00 às 13:00. Domingo e Feriados: Fechado."
                ),
                tags=["horario", "funcionamento", "abertura", "atendimento", "sabado", "domingo", "feriado"],
            ),
            PolicyChunk(
                chunk_id="sec_3",
                section_number="3",
                title="Formas de Pagamento e Parcelamento",
                content=(
                    "PIX: à vista com 5% de desconto sobre o preço de tabela. "
                    "Cartão de Débito: à vista. "
                    "Cartão de Crédito: em até 12x sem juros (parcela mínima de R$ 100,00). "
                    "Boleto Bancário: à vista, compensação em até 3 dias úteis. "
                    "Regras de Parcelamento: até 3x sem juros (sem mínimo exceto < R$ 50); 4x a 6x parcela mínima R$ 80; "
                    "7x a 12x parcela mínima R$ 100. Combinação de PIX + cartão permitida para compras acima de R$ 2.000,00."
                ),
                tags=["pagamento", "pix", "cartao", "credito", "debito", "boleto", "parcelamento", "desconto", "juros"],
            ),
            PolicyChunk(
                chunk_id="sec_4",
                section_number="4",
                title="Política de Trocas e Devoluções",
                content=(
                    "Direito de Arrependimento (Compras Online): até 7 (sete) dias corridos após o recebimento, sem necessidade de justificativa. "
                    "Embalagem original, sem sinais de uso, com manuais e acessórios. Reembolso na mesma forma de pagamento em até 10 dias úteis. "
                    "Frete de devolução por conta da loja em caso de arrependimento. "
                    "Trocas por Defeito: até 30 dias corridos após a compra. Após 30 dias, acionar garantia do fabricante. "
                    "Trocas por Preferência (cor/modelo): até 7 dias, produto em perfeito estado. "
                    "Itens não elegíveis para troca: produtos sob encomenda/personalizados, liquidação 'venda final', boquilhas de sopro."
                ),
                tags=["troca", "devolucao", "arrependimento", "defeito", "prazo", "reembolso", "frete", "7 dias", "30 dias"],
            ),
            PolicyChunk(
                chunk_id="sec_5",
                section_number="5",
                title="Política de Frete e Entregas",
                content=(
                    "Região Metropolitana de Campo Grande: Frete grátis para pedidos acima de R$ 500,00. Abaixo de R$ 500, taxa fixa de R$ 35,00. "
                    "Prazo: 1 a 3 dias úteis por motoboy próprio. "
                    "Outras Cidades: PAC (5 a 12 dias úteis), SEDEX (2 a 5 dias úteis), Jadlog (3 a 8 dias úteis). "
                    "Código de rastreamento enviado automaticamente: formato BR seguido de 9 caracteres alfanuméricos e BR."
                ),
                tags=["frete", "entrega", "prazo", "campo grande", "correios", "pac", "sedex", "jadlog", "rastreamento"],
            ),
            PolicyChunk(
                chunk_id="sec_6",
                section_number="6",
                title="Promoções e Descontos",
                content=(
                    "Aniversário da Loja (Agosto): 10% a 25%. Black Friday (Novembro): 15% a 30%. "
                    "Regras: promoções não são cumulativas. Desconto de PIX (5%) NÃO se aplica sobre preços já promocionais. "
                    "Produtos esgotados não geram reserva de preço. Promoções expiradas não são concedidas."
                ),
                tags=["promocao", "desconto", "black friday", "regras", "cumulativo"],
            ),
        ]

    def retrieve(self, query: str, top_k: int = 3) -> List[PolicyChunk]:
        """Retrieve most relevant policy sections for a given query."""
        if not self.chunks or not self._bm25:
            return []

        tokens = tokenize(query)
        if not tokens:
            return self.chunks[:top_k]

        scores = self._bm25.get_scores(tokens)
        scored_chunks = list(zip(self.chunks, scores))

        # Add boost for explicit query token match in tags or title
        boosted = []
        for chunk, score in scored_chunks:
            boost = 0.0
            query_lower = query.lower()
            for tag in chunk.tags:
                if tag in query_lower:
                    boost += 2.5
            if any(t in chunk.title.lower() for t in tokens):
                boost += 2.0
            boosted.append((chunk, score + boost))

        boosted.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in boosted[:top_k]]

    def format_retrieval_for_prompt(self, chunks: List[PolicyChunk]) -> str:
        """Format retrieved policy chunks into clean markdown context for the LLM."""
        if not chunks:
            return "Nenhuma política específica encontrada para esta consulta."

        formatted_sections = []
        for c in chunks:
            formatted_sections.append(
                f"### [Seção {c.section_number}] {c.title}\n{c.content}"
            )
        return "\n\n".join(formatted_sections)
