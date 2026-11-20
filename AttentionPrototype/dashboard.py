import datetime
import json
import streamlit as st
from streamlit_option_menu import option_menu
from attention_rules import process_attention_data  # processar dados de atenção
from attention_rules import get_latest_csv
import subprocess
import os
import signal
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd




PID_FILE = "process.pid"  # Arquivo para salvar o PID do processo de coleta


# Dicionário com categorias, softwares e descrições
software_categories = {
    "Produtividade": {
        "description": "Software used for coding and debugging",
        "apps": ["Visual Studio Code", "PyCharm", "Eclipse", "ChatGPT", "GitHub Desktop"]
    },
    "Documentos": {
        "description": "Tools for creating, viewing, and editing documents",
        "apps": ["Microsoft Word", "Microsoft Powerpoint", "Microsoft Excel", "Pré-Visualização", "Google Sheets", "Google Docs", "LaTeX"]
    },
    "Reuniões": {
        "description": "Platforms for video conferencing and online collaboration",
        "apps": ["Zoom", "Microsoft Teams", "Google Meet", "zoom.us"]
    },
    "Entretenimento": {
        "description": "Streaming and gaming platforms",
        "apps": ["YouTube", "Netflix", "Spotify", "Steam", "Epic Games Launcher", "Roblox"]
    },
    "Redes Sociais": {
        "description": "Social media and messaging platforms",
        "apps": ["Facebook", "Instagram", "TikTok", "WhatsApp"]
    },
    "Educação": {
        "description": "Educational platforms and tools",
        "apps": ["Coursera", "Moodle", "Udemy"]
    }
}



# 1. Página de Configuração de Preferências
def configure_preferences():
    st.title("Preference Settings")
    st.markdown(
        """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <p style="font-size: 13px; margin: 10px 0;">On this page, you can:</p>
            <ul style="font-size: 13px; padding-left: 20px;">
                <li>Select the software applications you consider useful for work or study (<b>Attentional Focus</b>).</li>
                <li>Configure headphone use and define how <b>music</b> affects your concentration.</li>
                <li>Configure your monitor arrangement to improve the analysis of <b>head position</b>.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Cria duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tools Selection")
        st.write("Select the software applications, organized by category, that you consider useful for work or study:")
        focus_apps = []

        category_translations = {
            "Produtividade": "Productivity",
            "Documentos": "Documents",
            "Reuniões": "Meetings",
            "Entretenimento": "Entertainment",
            "Redes Sociais": "Social Media",
            "Educação": "Education"
        }

        for category, details in software_categories.items():
            category_label = category_translations.get(category, category)

            st.markdown(
                f"<p style='color: #000000; font-size: 15px; font-weight: bold;'>{category_label}</p>",
                unsafe_allow_html=True
            )

            selected_apps_focus = st.multiselect(
                details["description"] + ":",
                details["apps"]
            )

            focus_apps.extend(selected_apps_focus)
        
    
    with col2:
        st.subheader("Website Domains")
        st.write("If you use Safari for work or study, add the allowed domains below (e.g., openai.com, google.com).")
        focus_urls = st.text_area("Enter domains separated by commas:", "").split(",")
        
        st.markdown("<br><br>", unsafe_allow_html=True)  # Quebras de linha

        st.subheader("Context")
        is_using_headphones = st.checkbox("I am using headphones", value=False)
        music_preference = st.radio(
            "How does music affect your focus?",
            options=["It helps me concentrate", "It distracts me", "It does not affect my focus"],
            index=2
        )

        st.markdown("<br><br>", unsafe_allow_html=True)  # Quebras de linha
    
        st.subheader("Monitors")
        num_monitors = st.number_input("How many monitors do you use?", min_value=1, max_value=3, step=1, value=1)
        monitor_positions = {}
        for i in range(1, num_monitors + 1):
            position = st.selectbox(f"Monitor {i} position:", ["Front", "Left", "Right", "Above"], key=f"monitor-{i}")
            monitor_positions[f"Monitor {i}"] = position
        st.markdown("<br>", unsafe_allow_html=True)  # Quebras de linha
    
    # Botão para salvar as preferências (fora das colunas para centralizar)
    col1_center, col2_center, col3_center = st.columns(3)
    with col2_center:
        if st.button("Save Preferences"):
            preferences = {
                "Monitores": monitor_positions,
                "Foco": focus_apps,
                "Contexto": {
                    "UsandoFones": is_using_headphones,
                    "PreferenciaMusica": music_preference
                },
                "FocoURLs": [url.strip() for url in focus_urls if url.strip()]
            }
            with open("user_preferences.json", "w") as f:
                json.dump(preferences, f, indent=4)
            st.success("Preferences saved successfully!")




# 2. Página para Iniciar a Coleta de Dados
def start_data_collection():
    st.title("Start/Stop Data Collection")
    st.write("Click the buttons below to start or stop the data collection process.")

    col1, col2 = st.columns(2)

    csv_path = None  # Inicializa a variável para evitar erro

    # Botão para Iniciar Coleta
    with col1:
        if st.button("Start Collection"):
            csv_path = get_latest_csv()  # Obtém o arquivo CSV mais recente


    # Botão para Parar Coleta
    with col2:
        if st.button("Stop Collection"):
            if not os.path.exists(PID_FILE):
                st.warning("No data collection is currently running.")
            else:
                try:
                    # Lê o PID do arquivo e encerra o processo
                    with open(PID_FILE, "r") as f:
                        pid = int(f.read())
                    os.kill(pid, signal.SIGTERM)  # Encerra o processo
                    os.remove(PID_FILE)  # Remove o arquivo PID
                    st.success("Data collection stopped.")
                except Exception as e:
                    st.error(f"Error stopping data collection: {e}")


    # Exibir os dados SOMENTE DEPOIS das colunas (fora delas)
    if csv_path:
        st.success("Example data loaded successfully!")

        try:
            # Carregar os dados do CSV
            data = pd.read_csv(csv_path)

            # Verifica se há dados no CSV antes de exibir
            if data.empty:
                st.warning("The CSV file is empty. No data available.")
            else:
                # Exibir uma mensagem informando que os dados são um exemplo
                #st.warning("Esses dados são um exemplo e não estão sendo coletados em tempo real.")

                # Exibir o DataFrame inteiro com rolagem automática
                st.dataframe(data, use_container_width=True, height=500)

        except Exception as e:
            st.error(f"Error loading data: {e}")

    else:
        # Verifica se já mostramos esse erro antes para evitar repetição
        if "csv_error_shown" not in st.session_state or not st.session_state.csv_error_shown:
            #st.warning("Nenhum arquivo de dados disponível no momento.")
            st.session_state.csv_error_shown = True  # Marca que a mensagem já foi mostrada

# 3. Página de Análise dos Dados
def analyze_data():
    st.title("Attention Data Analysis")
    print("--------------------------------------------------------")
    print("DATA", datetime.datetime.now())
    print("--------------------------------------------------------")

    # Criar colunas para alinhar botão e última atualização
    col1, col2 = st.columns([1, 1.5])

    # Inicializar a variável na sessão (se ainda não existir)
    if "last_update" not in st.session_state:
        st.session_state["last_update"] = None

    # Botão para iniciar análise
    with col1:
        if st.button("Analyze Recent Data"):
            st.session_state["show_graph"] = True  # Define variável de estado
            st.session_state["last_update"] = datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y')

    # Mostrar a última atualização ao lado
    with col2:
        with st.container():
            st.markdown(
                """
                <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    <p style="margin: auto; font-size: 16px; margin-left: -10px; margin-top: 5px;">
                        📅 <strong>Last updated:</strong> 
                        {last_update}
                    </p>
                </div>
                """.format(last_update=st.session_state["last_update"] if st.session_state["last_update"] else "Data has not been analyzed yet."),
                unsafe_allow_html=True
            )

    # Se o botão foi pressionado, exibir o gráfico
    if st.session_state.get("show_graph", False):
        # Criar um espaço para atualizar dinamicamente o gráfico
        graph_placeholder = st.empty()

        # Obtém os dados processados do attention_rules.py
        data, software_usage_time, sound_impact_data = process_attention_data()

        # DEBUG: Exibir os últimos 10 registros processados
        print("\n Dados antes de gerar o gráfico:")
        print(data.tail(10))  # Últimos 10 registros para análise
        print("\n ------  DADOS COMPLETOS - ANTES DE GERAR O GRAFICO:  --------")
        print(data.to_string())  # Exibir todos os registros sem truncamento

        if not data.empty:
            # Limpar gráfico anterior antes de renderizar o novo
            graph_placeholder.empty()

            # Preparar os dados para o gráfico
            timestamps = data.index
            attention_levels = data["Atento (%)"]
            attention_types = data["Tipo de Atenção"]

            # Traduções utilizadas exclusivamente nos tooltips
            state_translations = {
                "Atento": "Attentive",
                "Distraído": "Distracted"
            }
            
            head_position_translations = {
                "Olhando para Frente": "Looking Forward",
                "Olhando para a Esquerda": "Looking Left",
                "Olhando para a Direita": "Looking Right",
                "Olhando para Cima": "Looking Up",
                "Olhando para Baixo": "Looking Down",
                "Sem Detecção de Rosto": "No Face Detected"
            }
            
            sound_translations = {
                "Música": "Music",
                "Fala e Vozes": "Speech and Voices",
                "Ruídos de Fundo Neutros": "Neutral Background Noise",
                "Ruídos Intrusivos": "Intrusive Noise",
                "Natureza e Ambiente": "Nature and Environment",
                "Ruídos Mecânicos e Veiculares": "Mechanical and Vehicle Noise",
                "Ambiente Silencioso": "Quiet Environment",
                "Outros Sons": "Other Sounds",
                "Não Classificado": "Unclassified",
                "Irrelevante para Análise": "Not Relevant for Analysis"
            }
            
            attention_type_translations = {
                "Atenção": "Attention",
                "Atenção Alternada": "Alternating Attention",
                "Atenção Sustentada": "Sustained Attention",
                "Atenção Seletiva": "Selective Attention",
                "Distração": "Distraction",
                "Neutro": "Neutral"
            }

            attention_colors = {
                "Atenção": "#66C2A5",  # Verde suave
                "Atenção Alternada": "#8DA0CB",  # Azul lavanda
                "Atenção Sustentada": "#228B22",  # Verde escuro, enfatiza o alto foco
                "Atenção Seletiva": "#FFD92F",  # Amarelo claro (atenção com ruidos de fundo)
                "Distração": "#eb5f53",  # avermelhado
                "Neutro": "#B3B3B3"  # Cinza neutro
            }


            # Criar gráfico interativo com Plotly
            fig = go.Figure()

            # Adicionar linha principal do gráfico
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=attention_levels,
                mode="lines+markers",
                marker=dict(size=8, color="black", opacity=0.6),
                line=dict(width=2, color="black"),
                name="Attention Level",
                hoverinfo="skip"  # Isso remove o tooltip padrão da linha
            ))

            # Adicionar pontos coloridos e tooltips detalhados
            for i, timestamp in enumerate(timestamps):
                tipo_atencao = attention_types.iloc[i]
                cor = attention_colors.get(tipo_atencao, "gray")

                # Determinar corretamente o Estado de Atenção
                porcentagem_atencao = data.iloc[i]["Atento (%)"]
                porcentagem_distracao = data.iloc[i]["Distraído (%)"]

                if porcentagem_atencao > porcentagem_distracao:
                    estado = f"Atento ({porcentagem_atencao:.1f}%)"
                else:
                    estado = f"Distraído ({porcentagem_distracao:.1f}%)"

                # DEBUG: Exibir informações antes de plotar
                print(f"Plotando ponto -> Timestamp: {timestamp}, Atento (%): {porcentagem_atencao}, Tipo: {tipo_atencao}")

                # Criar tooltip com detalhes do bloco de tempo
                # Traduzir valores exclusivamente para exibição no tooltip
                estado_exibicao = state_translations.get(
                    estado.split(" (")[0],
                    estado.split(" (")[0]
                )
                
                estado_exibicao = f"{estado_exibicao} ({estado.split(' (')[1]}" if " (" in estado else estado_exibicao
                
                posicao_exibicao = head_position_translations.get(
                    data.iloc[i]["Posição Cabeça Mais Comum"],
                    data.iloc[i]["Posição Cabeça Mais Comum"]
                )
                
                som_exibicao = sound_translations.get(
                    data.iloc[i]["Som Predominante"],
                    data.iloc[i]["Som Predominante"]
                )
                
                tipo_exibicao = attention_type_translations.get(
                    tipo_atencao,
                    tipo_atencao
                )
                
                # Criar tooltip em inglês
                detalhes = (
                    f"⏰ {timestamp.strftime('%H:%M:%S')}<br>"
                    f"🎯 State: {estado_exibicao}<br>"
                    f"💻 Most Used Software: {data.iloc[i]['Software Mais Usado']}<br>"
                    f"👀 Most Frequent Head Position: {posicao_exibicao}<br>"
                    f"🔊 Predominant Sound: {som_exibicao}<br>"
                    f"🏷️ Attention Type: {tipo_exibicao}"
                )

                # Adicionar ponto ao gráfico com tooltip
                fig.add_trace(go.Scatter(
                    x=[timestamp],
                    y=[porcentagem_atencao],
                    mode="markers",
                    marker=dict(size=10, color=cor, line=dict(color="black", width=1)),
                    name=tipo_atencao,
                    text=detalhes,
                    hoverinfo="text",
                    showlegend=False  # Evita que as legendas se repitam
                ))

            # Configurar layout do gráfico
            fig.update_layout(
                title="Attention Over Time (Updated Every 30 Seconds)",
                xaxis_title="Time",
                yaxis_title="Attention Level (%)",
                yaxis=dict(range=[0, 105]),  # Pequena margem extra para evitar corte no 100%
                hovermode="closest",
                template="plotly_white"
            )

            # EXPLICAÇÃO DOS TIPOS DE ATENÇÃO EM UMA DIV ABAIXO DO GRÁFICO**
            st.markdown(
                """
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h4 style="font-size: 16px;">Attention State Classification</h4>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #1B9E77; font-weight: bold;">Sustained Attention:</span> Maintaining focus on an activity over an extended period without significant interruptions.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #8DA0CB; font-weight: bold;">Alternating Attention:</span> The ability to shift focus between different tasks while maintaining efficiency.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #FFD92F; font-weight: bold;">Selective Attention:</span> The ability to focus on a specific stimulus despite distractions in the environment.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #66C2A5; font-weight: bold;">Attention:</span> An adequate level of focus on the main activity, without frequent shifts or external interference.</p>
                    <p style="font-size: 13px;"><span style="color: #eb5f53; font-weight: bold;">Distraction:</span> Loss of attention due to external factors or difficulty maintaining engagement in the ongoing task.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Atualizar gráficos no Streamlit
            # Gráfico principal de atenção ao longo do tempo
            graph_placeholder.plotly_chart(fig, use_container_width=True)

            # Criar colunas de tamanhos diferentes (gráfico de barras maior)
            col1, col2 = st.columns([1.7, 1])

            # Adicionar o gráfico de softwares usados na coluna maior
            with col1:
                fig_bar = plot_most_used_software(software_usage_time)
                if fig_bar:
                    st.plotly_chart(fig_bar, use_container_width=True)

            # Adicionar o gráfico de pizza (Atenção x Distração) na coluna menor
            with col2:
                fig_pie = plot_attention_pie_chart(data)
                if fig_pie:
                    st.plotly_chart(fig_pie, use_container_width=True)

            # Adicionar o gráfico de impacto do som
            fig_sound = plot_sound_impact_chart(sound_impact_data)
            if fig_sound:
                st.plotly_chart(fig_sound, use_container_width=True)

        else:
            st.warning("There is no processed data available for analysis yet.")

        # Atualiza automaticamente a página a cada 30 segundos
        #now = datetime.datetime.now()
        #seconds = now.second

        # Espera até o próximo ciclo de 00 ou 30 segundos
        #sleep_time = 30 - seconds if seconds < 30 else 60 - seconds
        #time.sleep(sleep_time)
        #st.rerun()




# Criar gráfico de barras para softwares mais usados
def plot_most_used_software(software_usage_time):
    """
    Gera um gráfico de barras com os 3 softwares mais usados, mantendo um design mais limpo e profissional.
    """
    top_software = software_usage_time.nlargest(3)

    # Cores alternativas da paleta Set2 que não conflitam com o gráfico principal
    custom_colors_bar = ["#89A8B2", "#B3C8CF", "#E5E1DA", "#F1F0E8"]

    fig = px.bar(
        x=top_software.index,
        y=top_software.values,
        labels={"x": "Software", "y": "Usage Time (min)"},
        title="Software Usage Time",
        color=top_software.index,
        #color_discrete_sequence=px.colors.qualitative.Set2  # Paleta de cores Set2
        color_discrete_sequence=custom_colors_bar, 
    )

    # Melhorar rótulos e layout
    fig.update_traces(
        texttemplate='%{y:2f} min',  # tempo com 1 casa decimal
        textposition='outside',
        marker=dict(line=dict(width=0)),  # Remove bordas das barras
        hovertemplate='%{x}: %{y} min<extra></extra>'
    )

    fig.update_layout(
        showlegend=False,
        yaxis_title="Time (min)",
        xaxis_title="Softwares",
        xaxis_tickangle=0,
        yaxis=dict(
            tickformat=".2f", 
            showgrid=True, 
            range=[0, software_usage_time.max() * 1.2]  # Adiciona 20% extra para evitar corte
        ),
        margin=dict(t=60, b=50, l=50, r=50),
        width=650,  
        height=450  # Reduzindo a altura para um encaixe mais fluído
    )

    return fig




# Grafico de pizza para distribuição de atenção e distração
def plot_attention_pie_chart(grouped):
    """
    Gera um gráfico de pizza mostrando a distribuição total de atenção e distração.
    """
    if grouped.empty:
        st.warning("No data available for attention analysis.")
        return None

    # Calcular médias gerais de atenção e distração
    total_atento = grouped["Atento (%)"].mean()
    total_distraido = grouped["Distraído (%)"].mean()

    # Criar um DataFrame para o gráfico
    pie_data = {
        "Estado": ["Attentive", "Distracted"],
        "Porcentagem": [total_atento, total_distraido]
    }

    # Criar gráfico de pizza com Plotly
    fig = px.pie(
        pie_data,
        names="Estado",
        values="Porcentagem",
        title="Distribution of Attention and Distraction",
        color="Estado",
        color_discrete_map={"Attentive": "#66C2A5", "Distracted": "#eb5f53"}  # Verde para atenção, vermelho para distração
    )

    fig.update_traces(
        textfont=dict(family="Open Sans, Verdana, Arial, sans-serif", color="#ffffff"),
        marker=dict(line=dict(color="white", width=1)),  # Remove bordas indesejadas
        #hovertemplate="<b>%{label}</b><br>%{percent:.2%}<extra></extra>",
        hovertemplate='%{label}: %{percent:.2%} min<extra></extra>'
    )

    fig.update_layout(
        margin=dict(t=60),  # Margens uniformes
        showlegend=True,  # Exibir legenda
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="bottom",  # Ancorar na parte inferior
        )
    )

    return fig





# Criar gráfico de barras para impacto do som na atenção
def plot_sound_impact_chart(sound_impact_data):
    """
    Gráfico de barras refinado para mostrar o impacto do som no estado de atenção.
    """

    custom_colors_sound = ["#89A8B2", "#B3C8CF", "#E5E1DA", "#F1F0E8"]

    if sound_impact_data.empty:
        st.warning("No data available for sound impact analysis.")
        return None

    filtered_data = sound_impact_data[sound_impact_data["Distração Média (%)"] > 0]
    if filtered_data.empty:
        st.warning("No relevant sounds were identified as affecting attention.")
        return None

    # Tradução dos grupos de áudio exclusivamente para exibição
    sound_group_translations = {
        "Fala e Vozes": "Speech and Voices",
        "Ruídos de Fundo Neutros": "Neutral Background Noise",
        "Ruídos Intrusivos": "Intrusive Noise",
        "Natureza e Ambiente": "Nature and Environment",
        "Ruídos Mecânicos e Veiculares": "Mechanical and Vehicle Noise",
        "Ambiente Silencioso": "Quiet Environment",
        "Outros Sons": "Other Sounds",
        "Não Classificado": "Unclassified",
        "Irrelevante para Análise": "Not Relevant for Analysis"
    }

    # Criar uma cópia para apresentação, preservando os dados originais
    display_data = filtered_data.copy()
    
    display_data["Som Predominante"] = (
        display_data["Som Predominante"]
        .map(sound_group_translations)
        .fillna(display_data["Som Predominante"])
    )

    filtered_data = filtered_data.sort_values(by="Tempo Total do Som (min)", ascending=False)

    fig = px.bar(
        display_data,
        x="Tempo Total do Som (min)",
        y="Som Predominante",
        orientation="h",
        color="Som Predominante",
        color_discrete_sequence=custom_colors_sound,
        #color_discrete_sequence=px.colors.qualitative.Set2,  
        title="Estimated Duration of Sounds Affecting Attention",
        text="Tempo Total do Som (min)",  
    )

    fig.update_traces(
        texttemplate='%{x:.2f} min',
        textposition="outside",
        marker=dict(line=dict(width=0)),  # Remove bordas das barras
        hovertemplate='%{y}: %{x} min<extra></extra>'
    )

    fig.update_layout(
        xaxis_title="Estimated Duration (min)",
        yaxis_title="Predominant Sound",
        height=320,  
        width=750,  
        margin=dict(t=30, b=30, l=50, r=10),  # Redução das margens
        xaxis=dict(showgrid=True, range=[0, filtered_data["Tempo Total do Som (min)"].max() * 1.2]),
        showlegend=False  
    )

    return fig






# Menu de Navegação
def main_dashboard():
    # Mostrar o diretório atual no Streamlit Cloud
    # st.write("Diretório atual:", os.getcwd())
    # Adicionar o logo acima do menu
    logo_path = os.path.join(os.getcwd(), "AttentionPrototype", "logo.png")
    st.sidebar.image(logo_path)

    # Criar menu estilizado
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",  # Título do menu
            options=["Preferences", "Start Data Collection", "Analyze Data"],  # Opções do menu
            icons=["gear", "cloud-download", "graph-up"],  # Ícones correspondentes
            menu_icon="display",  # Ícone do título
            default_index=0,  # Aba padrão selecionada
            styles={
                "container": {"padding": "5px", "background-color": "#FAFAFA"},  # Cor de fundo do menu
                "icon": {"color": "black", "font-size": "20px"},  # Estilização dos ícones
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "5px",
                    "--hover-color": "#EEE",
                },
                "nav-link-selected": {"background-color": "#eb5f53", "color": "white"},  # Destaque para item selecionado
            }
        )


        # Conteúdo de cada aba
    if selected == "Preferences":
        configure_preferences()
    elif selected == "Start Data Collection":
        start_data_collection()
    elif selected == "Analyze Data":
        analyze_data()



if __name__ == "__main__":
    main_dashboard()
