# Exemplo 2: Informações Gerais da Loja Física e Horários de Atendimento

**Cenário:** Cliente querendo visitar a loja física em Campo Grande/MS para testar instrumentos e saber os horários no fim de semana.  
**Demonstração:** Recuperação RAG de políticas institucionais (Seção 1.2 e Seção 2 do Manual de Atendimento).

---

### Diálogo:

**Cliente:**
> Boa tarde! Queria dar uma passada aí para experimentar uns instrumentos. Qual o endereço da loja e qual o horário de funcionamento de vocês no sábado e domingo?

**Agente (Empório da Música):**
*(Executando ferramenta `get_store_info` e `consult_store_policies` com query "horário de funcionamento e atendimento sábado domingo")*

> Boa tarde! Vai ser um prazer enorme te receber aqui na nossa loja! Nada substitui a sensação de segurar o instrumento e ouvir o timbre ao vivo! 🎶
> 
> Seguem as nossas informações completas:
> 
> 📍 **Endereço:**  
> Rua 14 de Maio, 3200 — Centro, Campo Grande - MS (CEP 79202-333)  
> *Estamos bem no coração da cidade, com espaço climatizado para você testar com calma.*
> 
> 🕒 **Horários de Atendimento:**  
> • **Segunda a Sexta-feira:** das 09:00 às 18:00  
> • **Sábado:** das 09:00 às 13:00  
> • **Domingos e Feriados:** Fechado  
> 
> 📞 **Contatos Oficiais:**  
> Telefone / WhatsApp: (67) 3341-4444  
> E-mail: contato@emporiodamusica.com.br
> 
> Se vier no sábado, recomendo chegar um pouquinho antes do meio-dia para poder testar com tranquilidade. Tem algum instrumento específico que você gostaria que a gente deixasse separado para você tocar?
