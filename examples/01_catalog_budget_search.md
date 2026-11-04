# Exemplo 1: Consulta de Catálogo com Filtro de Preço e Categoria

**Cenário:** Cliente buscando opções de violões acústicos/clássicos até R$ 1.000,00 com disponibilidade imediata.  
**Demonstração:** Filtro estruturado no banco de dados SQLite, verificação de estoque real e apresentação no tom acolhedor da loja.

---

### Diálogo:

**Cliente:**
> Olá! Estou começando a tocar e gostaria de saber: quais opções de violões disponíveis vocês têm custando até R$1000?

**Agente (Empório da Música):**
*(Executando ferramenta `search_catalog` com argumentos `{"query": "violão", "category": "Violões", "max_price": 1000.0, "in_stock_only": true}`)*

> Opa, tudo bem? Que massa que você tá iniciando na música! Seja muito bem-vindo! 🎸🎶
> 
> Dei uma conferida no nosso catálogo agora e temos excelentes opções à pronta-entrega perfeitas para estudo e com ótima sonoridade, todas dentro do seu orçamento:
> 
> • **Tagima Memphis AC-39 Nylon Natural** — **R$ 429,90**  
>   *Violão clássico com cordas de nylon, corpo leve e super confortável para longas sessões de estudo. Ideal para iniciantes.* (Estoque: 15 unidades)
> 
> • **Rozini RC-104 Nylon Estudante** — **R$ 459,90**  
>   *Violão clássico de estudo da Rozini, produzido com madeiras nacionais de alta qualidade. Acabamento caprichado e afinação estável.* (Estoque: 10 unidades)
> 
> • **Shelby SN-100 Folk Aço Preto** — **R$ 549,00**  
>   *Violão folk de cordas de aço com visual moderno preto. Muito versátil para quem prefere uma pegada pop/rock.* (Estoque: 5 unidades)
> 
> • **Yamaha C40 Nylon Natural** — **R$ 599,90**  
>   *O clássico mundial para aprendizado! Tampo em Spruce, excelente projeção e padrão de qualidade Yamaha.* (Estoque: 12 unidades)
> 
> Lembrando que todos os instrumentos contam com garantia legal de 90 dias e você pode parcelar no cartão de crédito em até 12x sem juros (ou aproveitar 5% de desconto à vista no PIX!).
> 
> Você tem preferência por cordas de nylon (mais macias para quem tá começando) ou de aço? Me conta que te oriento no modelo ideal!
