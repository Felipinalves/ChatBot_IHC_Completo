import streamlit as st
from utils.time_utils import get_brasilia_time
from datetime import datetime, timedelta
import google.cloud.firestore as firestore

def generate_response_with_gemini(prompt):
    """
    Função stub para integração com o Gemini (ou outro modelo)
    Em um ambiente real, esta função chamaria a API do modelo
    """
    # Este é apenas um exemplo; em produção, você integraria com a API real
    return f"Resposta simulada sobre IHC para: {prompt.split('Pergunta:')[-1]}"

def show_chat_interface(query_engine, firestore_db, chat_id, messages):
    """Exibe a interface principal do chatbot"""
    
    st.title(f"🤖 IAHC ChatBot")
    st.info("Este chatbot utiliza RAG (Retrieval Augmented Generation) para fornecer respostas precisas sobre IHC.", icon="ℹ️")
    
    # Exibir mensagens anteriores
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Campo de entrada para nova mensagem
    if prompt := st.chat_input("Faça uma pergunta sobre IHC"):
        # Adicionar nova mensagem ao estado
        new_message = {
            "role": "user", 
            "content": prompt,
            "timestamp": get_brasilia_time(),
            "saved": False
        }
        messages.append(new_message)
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Verificar se é a primeira mensagem do usuário e atualizar o título do chat
        is_first_message = len([m for m in messages if m["role"] == "user"]) == 1
        
        # Atualizar título do chat se for a primeira mensagem
        if is_first_message and chat_id:
            # Limitar o tamanho do título para evitar títulos muito longos
            if len(prompt) > 50:
                new_chat_title = prompt[:47] + "..."
            else:
                new_chat_title = prompt
                
            # Atualizar título no Firestore e no estado da sessão
            chat_ref = firestore_db.collection("chats").document(chat_id)
            chat_ref.update({"title": new_chat_title})
            
            # Atualizar no estado da sessão
            if "chats" in st.session_state and chat_id in st.session_state.chats:
                st.session_state.chats[chat_id]["title"] = new_chat_title
        
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
                
                # Adicionar resposta ao estado
                new_response = {
                    "role": "assistant", 
                    "content": response,
                    "timestamp": get_brasilia_time(),
                    "saved": False
                }
                messages.append(new_response)
                
                with st.chat_message("assistant"):
                    st.write(response)
                
                # Salvar chat e mensagens no Firestore
                save_chat_to_firestore(firestore_db, chat_id, messages)
            
            status.update(label="Resposta gerada!", state="complete", expanded=False)

def save_chat_to_firestore(firestore_db, chat_id, messages):
    """
    Salva o chat e suas mensagens no Firestore
    
    Args:
        firestore_db: Cliente Firestore
        chat_id: ID do chat
        messages: Lista de mensagens
    """
    if not chat_id or "chats" not in st.session_state or chat_id not in st.session_state.chats:
        return
    
    # Atualizar timestamp do chat
    now = get_brasilia_time()
    chat_data = {
        "updated_at": now,
    }
    
    # Atualizar documento principal do chat
    chat_ref = firestore_db.collection("chats").document(chat_id)
    chat_ref.update(chat_data)
    
    # Adicionar mensagens não salvas à subcoleção
    for idx, msg in enumerate(messages):
        if not msg.get("saved", False):  # Apenas salva mensagens não salvas anteriormente
            msg_data = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", now),
                "order": idx  # Para manter a ordem das mensagens
            }
            chat_ref.collection("messages").add(msg_data)
            msg["saved"] = True  # Marca como salva

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
    
    if not chat_id:
        return messages
    
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
            "timestamp": msg_data.get("timestamp", get_brasilia_time()),
            "saved": True  # Marcar como já salva no Firestore
        })
    
    return messages

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
        "updated_at": now,
        "expiry_date": now + timedelta(days=30)  # Define data de expiração para 30 dias
    }
    
    # Adicionar documento à coleção de chats
    chat_ref = firestore_db.collection("chats").document()
    chat_ref.set(chat_data)
    
    return chat_ref.id

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

def cleanup_old_chats(firestore_db, days=30):
    """
    Remove chats e mensagens mais antigos que o número especificado de dias
    
    Args:
        firestore_db: Cliente Firestore
        days: Número de dias para manter os chats (padrão: 30)
    """
    now = get_brasilia_time()
    cutoff_date = now - timedelta(days=days)
    
    # Encontrar chats expirados
    expired_chats = firestore_db.collection("chats") \
                      .where("updated_at", "<", cutoff_date) \
                      .stream()
    
    batch_size = 0
    batch = firestore_db.batch()
    
    for chat in expired_chats:
        chat_ref = firestore_db.collection("chats").document(chat.id)
        
        # Excluir todas as mensagens primeiro
        messages = chat_ref.collection("messages").stream()
        for msg in messages:
            msg_ref = chat_ref.collection("messages").document(msg.id)
            batch.delete(msg_ref)
            batch_size += 1
            
            # Enviar batch quando atingir limite (500 é o máximo para firestore)
            if batch_size >= 450:
                batch.commit()
                batch = firestore_db.batch()
                batch_size = 0
        
        # Excluir o documento do chat
        batch.delete(chat_ref)
        batch_size += 1
        
        # Enviar batch quando atingir limite
        if batch_size >= 450:
            batch.commit()
            batch = firestore_db.batch()
            batch_size = 0
    
    # Enviar batch final se houver operações pendentes
    if batch_size > 0:
        batch.commit()
    
    print(f"Limpeza de chats antigos concluída: {now}")
