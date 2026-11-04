# Exemplo 4: Aplicação das Políticas de Troca e Devolução (Arrependimento em Compras Online)

**Cenário:** Cliente comprou um instrumento online, recebeu há 2 dias, mas se arrependeu e quer entender se pode devolver e como funciona o reembolso e frete.  
**Demonstração:** Situação não trivial combinando consulta RAG às diretrizes do Código de Defesa do Consumidor (Seção 4.1 do Manual) com verificação do pedido do cliente no banco de dados.

---

### Diálogo:

**Cliente:**
> Boa tarde. Comprei um violão pelo site de vocês e recebi anteontem, mas me arrependi da compra... Não me adaptei ao modelo. Eu posso devolver meu pedido e pegar meu dinheiro de volta? Como fica o frete de devolução? Meu pedido é o número 4 (ou rastreio BRQM7890123BR).

**Agente (Empório da Música):**
*(Executando ferramentas `consult_store_policies` com query "direito arrependimento prazo reembolso frete compras online" e `check_order_status` com rastreio "BRQM7890123BR")*

> Boa tarde, Lucas! Tudo bem? Fique tranquilo, estamos aqui justamente para te apoiar em qualquer situação! 😊
> 
> Localizei aqui o seu pedido **#4** (rastreio `BRQM7890123BR`), entregue recentemente.
> 
> De acordo com as nossas **Políticas de Trocas e Devoluções (Seção 4.1 do Manual e Art. 49 do CDC)**, você está **totalmente dentro do prazo**:
> 
> 1. **Prazo de Arrependimento:** Para compras realizadas online, você tem até **7 (sete) dias corridos** após o recebimento da mercadoria para solicitar a devolução sem qualquer necessidade de justificativa.
> 2. **Custo do Frete:** O frete de devolução é **100% por conta da Empório da Música**! Nós geramos uma autorização de logística reversa para você despachar sem custos.
> 3. **Condições do Produto:** O violão deve estar em sua embalagem original, sem sinais de uso ou desgaste, acompanhado de eventuais manuais e acessórios que vieram na caixa.
> 4. **Reembolso:** O estorno será efetuado na mesma forma de pagamento original (no seu caso, via boleto/conta bancária) em até **10 dias úteis** após a chegada e checagem do item em nossa expedição.
> 
> Se preferir, antes da devolução você também tem a opção de fazer uma **troca por preferência** por qualquer outro modelo do nosso catálogo (pagando ou recebendo a diferença).
> 
> Se desejar prosseguir com a devolução definitiva, me confirme por aqui que já aciono nossa equipe de atendimento para enviar a etiqueta de postagem no seu e-mail (`lucas.mendes@jmail.com`)!
