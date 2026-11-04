# Exemplo 3: Consulta de Preço, Especificações e Tratamento de Promoção Expirada

**Cenário:** Cliente perguntando o preço do violão Takamine GD20 e questionando sobre uma promoção que ouviu falar.  
**Demonstração:** Situação não trivial prevista no Manual (Seção 7.3): consulta ao banco de dados revelando preço de tabela (R$ 2.199,00) e uma promoção histórica inativa (`is_active = 0`), exigindo transparência ativa sem inventar descontos inválidos.

---

### Diálogo:

**Cliente:**
> Olá amigo! Quanto custa o Takamine GD20? Um amigo me falou que ele estava com 12% de desconto semana passada, essa promoção ainda tá valendo?

**Agente (Empório da Música):**
*(Executando ferramenta `get_product_details` com argumento `{"name_or_id": "Takamine GD20"}`)*

> Fala meu amigo! Beleza? O **Takamine GD20** é um verdadeiro monstro sonoro, escolha espetacular! 🎸✨
> 
> Sobre a promoção: fui direto no sistema consultar para você. Essa campanha de 12% OFF que seu amigo comentou foi uma **Oferta Especial pontual que já encerrou** no nosso sistema. Como prezamos pela total transparência com nossos clientes (e para não prometer nada fora das regras), o valor vigente hoje é o preço oficial de tabela:
> 
> • **Preço Atual:** **R$ 2.199,00**  
> • **Disponibilidade:** Temos **5 unidades em estoque** à pronta-entrega!
> 
> **Ficha Técnica rápida do GD20 Dreadnought:**
> • **Tampo:** Cedro Sólido (proporciona um timbre encorpado, quente e riquíssimo em harmônicos, sensacional para fingerstyle)  
> • **Fundo e Laterais:** Sapele  
> • **Braço:** Mogno com escala de 650mm  
> • **Cordas:** Aço  
> • **Acabamento:** Natural fosco elegante  
> 
> **Condições de Pagamento da Loja:**
> 💳 **Cartão de Crédito:** Em até **12x sem juros de R$ 183,25**  
> 💸 **PIX:** Pagamento à vista com **5% de desconto**, saindo por **R$ 2.089,05**!  
> 🚚 **Frete:** Se você for de Campo Grande, o frete é **100% grátis** via nosso motoboy (pedidos acima de R$ 500 têm entrega gratuita).
> 
> Quer que eu separe uma unidade para você ou tem alguma dúvida sobre a pegada do instrumento?
