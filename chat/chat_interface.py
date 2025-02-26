import streamlit as st

def show_chat_interface(query_engine, chat_id, messages):
    """Exibe a interface principal do chatbot"""
    
    if chat_id and chat_id in st.session_state.chats:
        st.title(f"🤖 {st.session_state.chats[chat_id]['title']}")
    else:
        st.title("Chatbot Especialista em IHC 🤖")
    
    st.info("Este chatbot utiliza RAG (Retrieval Augmented Generation) para fornecer respostas precisas sobre IHC.", icon="ℹ️")
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if prompt := st.chat_input("Faça uma pergunta sobre IHC"):
        messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.status("Processando sua pergunta...", expanded=True) as status:
            st.write("Buscando informações relevantes...")
            context = str(query_engine.query(prompt))
            
            st.write("Gerando resposta...")
            full_prompt = f"""Você é um especialista em IHC (Interação Humano-Computador) com vasta experiência acadêmica e prática.
Sua tarefa é fornecer respostas precisas e bem fundamentadas, baseadas no contexto fornecido.
[DIRETRIZES]
- Use português brasileiro formal
- Mantenha termos técnicos consolidados em inglês
- Organize a resposta em parágrafos claros e concisos
- Mencione autores/fontes quando relevante
[CONTEXTO]
{context}
Pergunta: {prompt}
Forneça uma resposta direta e bem estruturada, desenvolvendo a explicação com detalhes relevantes e concluindo com aspectos práticos. Se houver diferentes visões na literatura, apresente-as.
"""
            response = generate_response_with_gemini(full_prompt)
            
            if response:
                response = response.replace('[PERGUNTA]', '').replace('[RESPOSTA]', '').strip()
                messages.append({"role": "assistant", "content": response})
                
                with st.chat_message("assistant"):
                    st.write(response)
                
                if chat_id:
                    chat_data = {
                        "user_id": st.session_state.user_id,
                        "title": st.session_state.chats[chat_id]["title"],
                        "created_at": st.session_state.chats[chat_id]["created_at"],
                        "updated_at": get_brasilia_time(),
                        "messages": messages
                    }
                    save_chat_to_firebase(chat_id, chat_data)
            
            status.update(label="Resposta gerada!", state="complete", expanded=False)
