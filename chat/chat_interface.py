import streamlit as st
from utils.time_utils import get_brasilia_time

def show_chat_interface(query_engine, firestore_db, chat_id, messages):
    """Exibe a interface principal do chatbot"""
    
    # Verificar se há um chat atual
    if chat_id and chat_id in st.session_state.chats:
        st.title(f"🤖 IAHC Chatbot")
    
    st.info("Este chatbot utiliza RAG (Retrieval Augmented Generation) para fornecer respostas precisas sobre IHC.", icon="ℹ️")
    
    # Exibir mensagens anteriores
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Campo de entrada para nova mensagem
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
                
                # Salvar chat no Firestore se existir um chat_id
                if chat_id:
                    chat_data = {
                        "user_id": st.session_state.user_id,
                        "title": st.session_state.chats[chat_id]["title"],
                        "created_at": st.session_state.chats[chat_id]["created_at"],
                        "updated_at": get_brasilia_time(),
                    }
                    
                    # Atualizar documento principal do chat
                    chat_ref = firestore_db.collection("chats").document(chat_id)
                    chat_ref.set(chat_data, merge=True)
                    
                    # Adicionar mensagens à subcoleção
                    for idx, msg in enumerate(messages):
                        if not msg.get("saved", False):  # Apenas salva mensagens não salvas anteriormente
                            msg_data = {
                                "role": msg["role"],
                                "content": msg["content"],
                                "timestamp": get_brasilia_time(),
                                "order": idx  # Para manter a ordem das mensagens
                            }
                            chat_ref.collection("messages").add(msg_data)
                            msg["saved"] = True  # Marca como salva
            
            status.update(label="Resposta gerada!", state="complete", expanded=False)

# Função para carregar mensagens de um chat do Firestore
def load_chat_messages_from_firestore(firestore_db, chat_id):
    """
    Carrega as mensagens de um chat do Firestore
    
    Args:
        firestore_db: Cliente Firestore
        chat_id: ID do chat
        
    Returns:
        Lista de mensagens ordenadas
    """
    messages = []
    
    # Referência para a coleção de mensagens do chat
    message_refs = firestore_db.collection("chats").document(chat_id) \
                     .collection("messages") \
                     .order_by("order") \
                     .stream()
    
    # Converter documentos para o formato esperado
    for msg in message_refs:
        msg_data = msg.to_dict()
        messages.append({
            "role": msg_data["role"],
            "content": msg_data["content"],
            "saved": True  # Marcar como já salva no Firestore
        })
    
    return messages

# Função para salvar novo chat no Firestore
def create_new_chat_in_firestore(firestore_db, user_id, title):
    """
    Cria um novo chat no Firestore
    
    Args:
        firestore_db: Cliente Firestore
        user_id: ID do usuário
        title: Título do chat
        
    Returns:
        ID do chat criado
    """
    now = get_brasilia_time()
    
    # Dados do novo chat
    chat_data = {
        "user_id": user_id,
        "title": title,
        "created_at": now,
        "updated_at": now
    }
    
    # Adicionar documento à coleção de chats
    chat_ref = firestore_db.collection("chats").document()
    chat_ref.set(chat_data)
    
    return chat_ref.id

# Função para listar todos os chats de um usuário
def list_user_chats_from_firestore(firestore_db, user_id):
    """
    Lista todos os chats de um usuário
    
    Args:
        firestore_db: Cliente Firestore
        user_id: ID do usuário
        
    Returns:
        Dicionário de chats com ID como chave
    """
    chats = {}
    
    # Consultar chats do usuário
    chat_refs = firestore_db.collection("chats") \
                  .where("user_id", "==", user_id) \
                  .order_by("updated_at", direction="DESCENDING") \
                  .stream()
    
    # Converter para dicionário
    for chat in chat_refs:
        chat_data = chat.to_dict()
        chats[chat.id] = chat_data
    
    return chats
