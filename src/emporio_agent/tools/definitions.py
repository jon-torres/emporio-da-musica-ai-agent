import json
from typing import Any, Dict, List, Optional
from emporio_agent.db.database import Database
from emporio_agent.rag.retriever import PolicyRetriever


class ToolRegistry:
    """Provides tools for the agent to query database and policy RAG."""

    def __init__(self, db: Optional[Database] = None, retriever: Optional[PolicyRetriever] = None):
        self.db = db or Database()
        self.retriever = retriever or PolicyRetriever()

    def search_catalog(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        in_stock_only: bool = True,
        limit: int = 15,
    ) -> str:
        """Busca produtos no catálogo da Empório da Música por termo/modelo (ex: 'Takamine', 'violão', 'yamaha', 'nylon'), categoria, faixa de preço e estoque."""
        products = self.db.search_products(
            query=query,
            category=category,
            max_price=max_price,
            min_price=min_price,
            in_stock_only=in_stock_only,
            limit=limit,
        )

        if not products:
            return "Nenhum produto encontrado com os filtros especificados."

        results = []
        for p in products:
            price_text = f"R$ {p.price_brl:.2f}"
            if p.promotional_price:
                price_text = f"R$ {p.promotional_price:.2f} (de R$ {p.price_brl:.2f} - {p.active_discount_percent}% OFF)"

            results.append({
                "product_id": p.product_id,
                "nome": p.name,
                "categoria": p.category_name,
                "preco": price_text,
                "estoque": p.stock_quantity,
                "descricao": p.description,
            })

        return json.dumps(results, ensure_ascii=False, indent=2)

    def get_product_details(self, name_or_id: str) -> str:
        """Obtém preço atual, especificações técnicas, estoque e informações de promoções ativas/expiradas de um instrumento musical pelo nome (ex: 'Takamine GD20', 'Yamaha C40') ou ID."""
        name_or_id_str = str(name_or_id).strip()
        product = None

        if name_or_id_str.isdigit():
            product = self.db.get_product_by_id(int(name_or_id_str))
        else:
            product = self.db.get_product_by_name(name_or_id_str)

        if not product:
            return f"Produto '{name_or_id}' não encontrado no catálogo."

        promo_history = self.db.get_product_promotions_history(product.product_id)
        active_promo = next((p for p in promo_history if p.is_active), None)
        expired_promos = [p for p in promo_history if not p.is_active]

        details = {
            "id": product.product_id,
            "nome": product.name,
            "categoria": product.category_name,
            "preco_tabela": f"R$ {product.price_brl:.2f}",
            "preco_promocional": f"R$ {product.promotional_price:.2f}" if product.promotional_price else None,
            "desconto_ativo": f"{product.active_discount_percent}%" if product.active_discount_percent else None,
            "estoque": product.stock_quantity,
            "status": product.status,
            "descricao": product.description,
            "especificacoes": product.specs,
            "promocoes_ativas": [p.description for p in promo_history if p.is_active],
            "promocoes_expiradas": [f"{p.description} ({p.discount_percent}% OFF - VENCIDA)" for p in expired_promos],
        }
        return json.dumps(details, ensure_ascii=False, indent=2)

    def check_order_status(
        self,
        tracking_code: Optional[str] = None,
        order_id: Optional[int] = None,
        customer_query: Optional[str] = None,
    ) -> str:
        """Consulta status, prazo estimado, rastreio e itens de um pedido de cliente."""
        order = None
        if tracking_code:
            order = self.db.get_order_by_tracking(tracking_code)
        elif order_id:
            order = self.db.get_order_by_id(order_id)

        if order:
            return json.dumps({
                "pedido_id": order.order_id,
                "cliente": order.customer_name,
                "data": order.order_date,
                "status": order.status,
                "total": f"R$ {order.total_brl:.2f}",
                "forma_pagamento": order.payment_method,
                "codigo_rastreio": order.tracking_code,
                "previsao_entrega": order.estimated_delivery,
                "observacoes": order.notes,
                "itens": [
                    {"produto": item.product_name, "quantidade": item.quantity, "preco_unitario": f"R$ {item.unit_price:.2f}"}
                    for item in order.items
                ],
            }, ensure_ascii=False, indent=2)

        if customer_query:
            orders = self.db.get_customer_orders(customer_query)
            if orders:
                summary = []
                for o in orders:
                    summary.append({
                        "pedido_id": o.order_id,
                        "cliente": o.customer_name,
                        "data": o.order_date,
                        "status": o.status,
                        "total": f"R$ {o.total_brl:.2f}",
                        "rastreio": o.tracking_code,
                    })
                return json.dumps(summary, ensure_ascii=False, indent=2)

        return "Nenhum pedido encontrado com os dados informados."

    def consult_store_policies(self, query: str) -> str:
        """Consulta as políticas oficiais da loja no manual: trocas, devoluções, formas de pagamento, parcelamento, prazos e fretes."""
        chunks = self.retriever.retrieve(query, top_k=3)
        return self.retriever.format_retrieval_for_prompt(chunks)

    def get_store_info(self) -> str:
        """Retorna informações institucionais, endereço físico, horário de atendimento e contatos oficiais."""
        chunks = self.retriever.retrieve("endereço horário contato", top_k=2)
        return self.retriever.format_retrieval_for_prompt(chunks)

    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions of tools for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_catalog",
                    "description": "Busca produtos no catálogo da loja por termo, categoria e limite de preço.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Termo de busca, nome do instrumento ou características (ex: 'violão', 'tagima', 'nylon')."},
                            "category": {"type": "string", "description": "Categoria específica (ex: 'Violões', 'Guitarras', 'Baixos', 'Teclados e Pianos')."},
                            "max_price": {"type": "number", "description": "Preço máximo em reais (ex: 1000.0)."},
                            "min_price": {"type": "number", "description": "Preço mínimo em reais."},
                            "in_stock_only": {"type": "boolean", "description": "Filtrar apenas itens com estoque disponível (padrão true)."},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product_details",
                    "description": "Consulta especificações detalhadas, preço atual, estoque e promoções de um instrumento específico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name_or_id": {"type": "string", "description": "Nome ou ID do produto (ex: 'Takamine GD20' ou '95')."},
                        },
                        "required": ["name_or_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_order_status",
                    "description": "Consulta o status e rastreamento de um pedido pelo código de rastreio, número do pedido ou nome do cliente.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tracking_code": {"type": "string", "description": "Código de rastreamento (ex: 'BRQM7890123BR')."},
                            "order_id": {"type": "integer", "description": "Número de identificação do pedido (ex: 4)."},
                            "customer_query": {"type": "string", "description": "Nome, e-mail ou telefone do cliente."},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consult_store_policies",
                    "description": "Consulta as políticas da loja sobre trocas, devoluções, arrependimento, frete, formas de pagamento e garantias.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Dúvida ou tema da política (ex: 'prazo devolução arrependimento', 'frete campo grande', 'parcelamento sem juros')."},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_store_info",
                    "description": "Retorna o endereço físico da loja em Campo Grande, horários de funcionamento e canais de contato.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]
