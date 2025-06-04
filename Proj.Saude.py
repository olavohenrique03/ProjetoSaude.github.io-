# Importa bibliotecas essenciais para o projeto
import mysql.connector
import tkinter as tk
from tkinter import ttk
import customtkinter
from CTkMessagebox import CTkMessagebox  
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

# Estabelecer conexão com o banco de dados MySQL
try:
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="projsaude",
    )
    cursor = conexao.cursor()
except mysql.connector.Error as err:
    print(f"Erro ao conectar ao MySQL: {err}")


# Função que exibe o menu principal com botões para acessar os módulos
def frmMenu():
    global janelaMenu
    janelaMenu = customtkinter.CTk()
    janelaMenu.title("Modulo principal - clinica medica")
    janelaMenu.geometry("500x600+425+50")
    janelaMenu.resizable(False, False)

    frame_0 = customtkinter.CTkFrame(janelaMenu)
    frame_0.place(relx=0.5, rely=0.5, anchor="center")

    botoes = [
        ("Pacientes", frmPac),
        ("Médico", frmMed),
        ("Consultas", frmCons),
    ]

    for i, (texto, comando) in enumerate(botoes):
        btn = customtkinter.CTkButton(
            frame_0, text=texto, font=("Helvetica", 12, "bold"), command=comando, width=200
        )
        btn.grid(row=i, column=0, padx=20, pady=20)

    janelaMenu.mainloop()

# Formulário Paciente
def frmPac():
    def enviar_mensagem():
        mensagem = entrada_mensagem.get().strip()
        if not mensagem:
            return

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        chat_textbox.configure(state="normal")
        chat_textbox.insert("end", f"[{data_hora}]\nVocê: {mensagem}\n\n", "usuario")

        resposta = responder_chatbot(mensagem)
        data_hora_resp = datetime.now().strftime("%d/%m/%Y %H:%M")
        chat_textbox.insert("end", f"[{data_hora_resp}]\nChatbot-AI: {resposta}\n\n", "chatbot")

        chat_textbox.configure(state="disabled")
        chat_textbox.see("end")
        entrada_mensagem.delete(0, "end")

    # Função que processa a lógica de interação com o chatbot
    def responder_chatbot(mensagem):
        mensagem = mensagem.strip()
        estado = etapa_cadastro["estado"]

        # Cadastro
        if etapa_cadastro["modo"] == "cadastro" and estado:
            chaves = [
                "nome", "datanascimento", "cpf",
                "telcontato", "convenio", "numconvenio"
            ]
            prompts = [
                "Qual a sua data de nascimento?",
                "Qual o seu CPF?",
                "Qual o seu telefone de contato?",
                "Qual o seu convenio?",
                "Qual o seu numero do convenio?"
            ]
            index = chaves.index(estado)

            if estado == "datanascimento":
                try:
                    datetime.strptime(mensagem, "%Y-%m-%d")  
                except ValueError:
                    return "Formato de data inválido. Use o formato YYYY-MM-DD (ex: 1990-01-31)."

            etapa_cadastro["dados"][estado] = mensagem
            if index + 1 < len(chaves):
                etapa_cadastro["estado"] = chaves[index + 1]
                return prompts[index]
            else:
                dados = etapa_cadastro["dados"]
                
                try:
                    sql = """
                        INSERT INTO paciente (nome, datanascimento, cpf, telcontato, convenio, numconvenio)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    valores = (
                        dados["nome"],
                        dados["datanascimento"],  
                        dados["cpf"],
                        dados["telcontato"],
                        dados["convenio"],
                        dados["numconvenio"]
                    )
                    cursor.execute(sql, valores)
                    conexao.commit()
                    etapa_cadastro["estado"] = None
                    etapa_cadastro["modo"] = None
                    return "Cadastro realizado com sucesso no banco de dados!\n\n 1 - Cadastrar Paciente.\n 2 - Alterar Paciente.\n 3 - Consultar Paciente.\n 4 - Excluir Paciente.\n 5 - Finalizar Atendimento. \n\n"
                    
                except mysql.connector.Error as erro:
                    return f"Erro ao cadastrar no banco: {erro}"

        # Alteração
        if etapa_cadastro["modo"] == "alterar" and estado:
            if estado == "cpf":
                etapa_cadastro["cpf"] = mensagem
                etapa_cadastro["estado"] = "nome"
                return "Novo nome:"
            
            etapa_cadastro["dados"][estado] = mensagem
            chaves = ["nome", "datanascimento", "telcontato", "convenio", "numconvenio"]
            prompts = [
                "Nova data de nascimento:",
                "Novo telefone:",
                "Novo convênio:",
                "Novo número do convênio:"
            ]
            index = chaves.index(estado)
            if index + 1 < len(chaves):
                etapa_cadastro["estado"] = chaves[index + 1]
                return prompts[index]
            else:
                dados = etapa_cadastro["dados"]

                try:
                    
                    cursor.execute("SELECT * FROM paciente WHERE cpf = %s", (etapa_cadastro["cpf"],))
                    if not cursor.fetchone():
                        etapa_cadastro["modo"] = None
                        etapa_cadastro["estado"] = None
                        return "CPF não encontrado. Não foi possível alterar os dados."

                    
                    sql = """
                        UPDATE paciente
                        SET nome = %s, datanascimento = %s, telcontato = %s, convenio = %s, numconvenio = %s
                        WHERE cpf = %s
                    """
                    valores = (
                        dados["nome"],
                        dados["datanascimento"],
                        dados["telcontato"],
                        dados["convenio"],
                        dados["numconvenio"],
                        etapa_cadastro["cpf"]  
                    )
                    cursor.execute(sql, valores)
                    conexao.commit()
                    etapa_cadastro["estado"] = None
                    etapa_cadastro["modo"] = None
                    return "Alteração realizada com sucesso no banco de dados!\n\n 1 - Cadastrar Paciente.\n 2 - Alterar Paciente.\n 3 - Consultar Paciente.\n 4 - Excluir Paciente.\n 5 - Finalizar Atendimento. \n\n"
                except mysql.connector.Error as erro:
                    return f"Erro ao alterar no banco: {erro}"

        # Exclusão
        if etapa_cadastro["modo"] == "excluir" and estado == "cpf":
            cpf = mensagem
            try:
                cursor.execute("SELECT * FROM paciente WHERE cpf = %s", (cpf,))
                if cursor.fetchone():
                    cursor.execute("DELETE FROM paciente WHERE cpf = %s", (cpf,))
                    conexao.commit()
                    etapa_cadastro["modo"] = None
                    etapa_cadastro["estado"] = None
                    return "Paciente excluído com sucesso do banco de dados!\n\n 1 - Cadastrar Paciente.\n 2 - Alterar Paciente.\n 3 - Consultar Paciente.\n 4 - Excluir Paciente.\n 5 - Finalizar Atendimento. \n\n"
                else:
                    return "Paciente não encontrado para exclusão."
            except mysql.connector.Error as erro:
                return f"Erro ao excluir: {erro}"

        # Comandos principais
        comandos = {
            "1": ("cadastro", "nome", "Vamos iniciar o cadastro.\nQual seu nome completo?"),
            "2": ("alterar", "cpf", "Digite o CPF do paciente a ser alterado:"),
            "3": ("consultar", "cpf", "Digite o CPF do paciente a ser consultado:"),
            "4": ("excluir", "cpf", "Digite o CPF do paciente a ser excluído:"),
            "5": (None, None, "Atendimento encerrado. Volte sempre!"), 
        }

        if mensagem in comandos:
            modo, estado, resposta, *acao = comandos[mensagem]
            etapa_cadastro["modo"] = modo
            etapa_cadastro["estado"] = estado
            etapa_cadastro["dados"] = {}
            if modo == "alterar":
                return "Digite o CPF do paciente a ser alterado:"
            if acao:
                acao[0]()
            return resposta

        # Consulta
        if etapa_cadastro["modo"] == "consultar" and etapa_cadastro["estado"] == "cpf":
            cpf = mensagem
            try:
                cursor.execute("SELECT * FROM paciente WHERE cpf = %s", (cpf,))
                paciente = cursor.fetchone()
                if paciente:
                    etapa_cadastro["modo"] = None
                    etapa_cadastro["estado"] = None
                    return (
                        f"Paciente encontrado:\n"
                        f"Nome: {paciente[1]}\n"
                        f"Data de Nascimento: {paciente[2]}\n"
                        f"CPF: {paciente[3]}\n"
                        f"Telefone: {paciente[4]}\n"
                        f"Convênio: {paciente[5]}\n"
                        f"Nº Convênio: {paciente[6]}\n\n\n 1 - Cadastrar Paciente.\n 2 - Alterar Paciente.\n 3 - Consultar Paciente.\n 4 - Excluir Paciente.\n 5 - Finalizar Atendimento. \n\n"
                    )
                else:
                    etapa_cadastro["modo"] = None
                    etapa_cadastro["estado"] = None
                    return "Paciente não encontrado."
            except mysql.connector.Error as erro:
                return f"Erro ao consultar: {erro}"


        return "Desculpe, não entendi. Poderia reformular sua pergunta?"

    global janelaPac
    etapa_cadastro = {"modo": None, "estado": None, "dados": {}}
    

    janelaPac = customtkinter.CTk()
    janelaPac.title("Módulo Secundário - Clínica Médica [Pacientes]!")
    janelaPac.geometry("500x600+425+50")
    janelaPac.resizable(False, False)

    frame_0 = customtkinter.CTkFrame(janelaPac)
    frame_0.pack(pady=10, padx=10, fill="both", expand=True)

    chat_textbox = customtkinter.CTkTextbox(frame_0, height=400, state="normal", wrap="word")
    chat_textbox.pack(padx=10, pady=(10, 5), fill="both", expand=True)
    chat_textbox.tag_config("usuario", foreground="#3B8ED0", justify="left")
    chat_textbox.tag_config("chatbot", foreground="white")

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    chat_textbox.insert(
        customtkinter.END,
        f"[{data_hora}]\nChatbot-AI: Olá sou o seu ChatBot e vou te ajudar hoje! \nO que deseja:\n\n 1 - Cadastrar Paciente.\n 2 - Alterar Paciente.\n 3 - Consultar Paciente.\n 4 - Excluir Paciente.\n 5 - Finalizar Atendimento. \n\n",
        "chatbot"
    )
    chat_textbox.configure(state="disabled")

    frame_input = customtkinter.CTkFrame(frame_0)
    frame_input.pack(padx=10, pady=10, fill="x")

    entrada_mensagem = customtkinter.CTkEntry(frame_input, placeholder_text="Digite sua mensagem...")
    entrada_mensagem.pack(side="left", fill="x", expand=True, padx=(0, 10))
    entrada_mensagem.bind("<Return>", lambda event: enviar_mensagem())

    botao_enviar = customtkinter.CTkButton(frame_input, text="Enviar", command=enviar_mensagem)
    botao_enviar.pack(side="right")

    janelaPac.mainloop()


# Formulário Médico
def frmMed():
    janelaMed = customtkinter.CTk()
    janelaMed.title("Cadastro de Médicos")
    janelaMed.geometry("700x500+400+100")
    janelaMed.resizable(False, False)

    frame = customtkinter.CTkFrame(janelaMed)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    titulo = customtkinter.CTkLabel(frame, text="Médicos Disponíveis", font=("Helvetica", 16, "bold"))
    titulo.pack(pady=10)

    tabela_frame = tk.Frame(frame, bg="#2b2b2b")
    tabela_frame.pack(padx=10, pady=10, fill="both", expand=True)

    colunas = ("nome", "especialidade", "horario")
    tabela = ttk.Treeview(tabela_frame, columns=colunas, show="headings", style="Dark.Treeview")
    tabela.heading("nome", text="Nome")
    tabela.heading("especialidade", text="Especialidade")
    tabela.heading("horario", text="Horário Disponível")

    tabela.column("nome", anchor="center")
    tabela.column("especialidade", anchor="center")
    tabela.column("horario", anchor="center")

    tabela.pack(fill="both", expand=True)

    # Função para mostrar grafo das especialidades
    def exibir_grafo_especialidades():
        grafo_especialidades = {
            "Cardiologia": ["Pneumologia", "Endocrinologia"],
            "Pneumologia": ["Cardiologia", "Alergologia"],
            "Endocrinologia": ["Cardiologia"],
            "Alergologia": ["Pneumologia"],
            "Neurologia": ["Psiquiatria"],
            "Psiquiatria": ["Neurologia"],
        }

        G = nx.Graph()
        for especialidade, conexoes in grafo_especialidades.items():
            for conexao in conexoes:
                G.add_edge(especialidade, conexao)

        plt.figure(figsize=(8, 6))
        nx.draw(G, with_labels=True, node_color='skyblue', node_size=2500, font_size=10, font_weight='bold')
        plt.title("Grafo de Especialidades Médicas")
        plt.show()

    botoes_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
    botoes_frame.pack(pady=10)

    btn_voltar = customtkinter.CTkButton(botoes_frame, text="Voltar", width=120, command=janelaMed.destroy)
    btn_voltar.pack(side="left", padx=20)

    btn_grafo = customtkinter.CTkButton(botoes_frame, text="Mostrar Grafo", width=120, command=exibir_grafo_especialidades)
    btn_grafo.pack(side="left", padx=20)

    def agendar_consulta():
        item_selecionado = tabela.focus()
        if not item_selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um médico para agendar.", icon="warning")
            return

        medico_id = int(item_selecionado)  
        frmCons(medico_id)

    botao_agendar = customtkinter.CTkButton(janelaMed, text="Agendar Consulta", command=agendar_consulta)
    botao_agendar.pack(pady=10)

    # Função para carregar os dados do banco
    def carregar_dados():
        try:
            cursor.execute("SELECT id_medico, nome, especialidade, horario_disponivel FROM medico")
            dados = cursor.fetchall()
            for linha in dados:
                id_medico, nome, especialidade, horario = linha
                tabela.insert("", "end", iid=id_medico, values=(nome, especialidade, horario))
        except Exception as erro:
            CTkMessagebox(title="Erro", message=f"Erro ao carregar dados: {erro}", icon="cancel")

    carregar_dados()
    janelaMed.mainloop()


# Formulário Consulta
def frmCons(medico_id=None):
    janelaCons = customtkinter.CTk()
    janelaCons.title("Consultas - Clínica Médica")
    janelaCons.geometry("800x600+400+100")
    janelaCons.resizable(False, False)

    frame_tabela = customtkinter.CTkFrame(
        janelaCons, corner_radius=10, border_width=2, border_color="#3B8ED0"
    )
    frame_tabela.pack(padx=20, pady=20, fill="both", expand=True)

    colunas = ["ID", "ID Paciente", "ID Médico", "DATA HORA"]

    for i in range(len(colunas)):
        frame_tabela.grid_columnconfigure(i, weight=1, uniform="coluna")

    for i, col in enumerate(colunas):
        lbl = customtkinter.CTkLabel(
            frame_tabela,
            text=col,
            font=("Helvetica", 13, "bold"),
            text_color="#FFFFFF",
            fg_color="#3B8ED0",
            corner_radius=4,
            anchor="center",
            width=150
        )
        lbl.grid(row=0, column=i, padx=5, pady=8, sticky="nsew")

    # Dados da tabela
    try:
        cursor.execute("SELECT id, id_paciente, id_medico, data_hora FROM consulta")
        resultados = cursor.fetchall()

        for row_idx, row in enumerate(resultados, start=1):
            for col_idx, item in enumerate(row):
                lbl = customtkinter.CTkLabel(
                    frame_tabela,
                    text=str(item),
                    anchor="center",
                    font=("Helvetica", 12)
                )
                lbl.grid(row=row_idx, column=col_idx, padx=5, pady=4, sticky="nsew")
    except mysql.connector.Error as erro:
        CTkMessagebox(title="Erro", message=f"Erro ao buscar consultas: {erro}", icon="cancel")

    # Área de agendamento
    if medico_id:
        frame_agendamento = customtkinter.CTkFrame(
            janelaCons, corner_radius=10, border_width=2, border_color="#3B8ED0"
        )
        frame_agendamento.pack(padx=20, pady=10, fill="x")

        cursor.execute("SELECT nome, horario_disponivel FROM medico WHERE id_medico = %s", (medico_id,))
        medico_info = cursor.fetchone()

        if not medico_info:
            CTkMessagebox(title="Erro", message="Médico não encontrado!", icon="cancel")
            janelaCons.destroy()
            return

        nome_medico, horario_disponivel = medico_info

        customtkinter.CTkLabel(frame_agendamento, text=f"Médico: {nome_medico}", font=("Helvetica", 13, "bold")).pack(pady=5)
        customtkinter.CTkLabel(frame_agendamento, text=f"Horário Disponível: {horario_disponivel}", font=("Helvetica", 12)).pack(pady=2)

        customtkinter.CTkLabel(frame_agendamento, text="CPF do Paciente:", font=("Helvetica", 12)).pack(pady=(10, 2))
        campo_cpf = customtkinter.CTkEntry(frame_agendamento, height=30)
        campo_cpf.pack(pady=2)

        customtkinter.CTkLabel(frame_agendamento, text="Data da Consulta (AAAA-MM-DD):", font=("Helvetica", 12)).pack(pady=(10, 2))
        campo_data = customtkinter.CTkEntry(frame_agendamento, height=30)
        campo_data.pack(pady=2)

        def agendar():
            cpf_paciente = campo_cpf.get().strip()
            data_consulta = campo_data.get().strip()
            data_hora = f"{data_consulta} {horario_disponivel}"

            try:
                cursor.execute("SELECT id_paciente FROM paciente WHERE cpf = %s", (cpf_paciente,))
                resultado = cursor.fetchone()
                if not resultado:
                    CTkMessagebox(title="Erro", message="Paciente não encontrado!", icon="cancel")
                    return

                id_paciente = resultado[0]

                cursor.execute(
                    "INSERT INTO consulta (id_paciente, id_medico, data_hora) VALUES (%s, %s, %s)",
                    (id_paciente, medico_id, data_hora)
                )
                conexao.commit()
                CTkMessagebox(title="Sucesso", message="Consulta agendada com sucesso!", icon="check")
                janelaCons.destroy()
                frmCons()  # Atualiza a tela
            except mysql.connector.Error as err:
                CTkMessagebox(title="Erro", message=f"Erro ao agendar: {err}", icon="cancel")

        customtkinter.CTkButton(
            frame_agendamento,
            text="Confirmar Agendamento",
            command=agendar,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(pady=15)

    janelaCons.mainloop()

# Formulário Login
usuarios = {}

def frmLogin():
    def autenticar():
        email = entrada_email.get().strip()
        senha = entrada_senha.get().strip()

        if not email or not senha:
            resultado_label.configure(text="Preencha todos os campos.", text_color="red")
            return

        if email in usuarios:
            if usuarios[email] == senha:
                resultado_label.configure(text="Login realizado com sucesso!", text_color="green")
                janelaLogin.after(1000, lambda: [janelaLogin.destroy(), frmMenu()])
            else:
                resultado_label.configure(text="Senha incorreta.", text_color="red")
        else:
            usuarios[email] = senha
            resultado_label.configure(text="Cadastro realizado com sucesso!", text_color="green")
            janelaLogin.after(1000, lambda: [janelaLogin.destroy(), frmMenu()])

    janelaLogin = customtkinter.CTk()
    janelaLogin.title("Login - Clínica Médica")
    janelaLogin.geometry("400x300+500+200")
    janelaLogin.resizable(False, False)

    frame = customtkinter.CTkFrame(janelaLogin)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    entrada_email = customtkinter.CTkEntry(frame, placeholder_text="Email")
    entrada_email.pack(pady=10, fill="x")

    entrada_senha = customtkinter.CTkEntry(frame, placeholder_text="Senha", show="*")
    entrada_senha.pack(pady=10, fill="x")

    resultado_label = customtkinter.CTkLabel(frame, text="")
    resultado_label.pack(pady=5)

    botao_login = customtkinter.CTkButton(frame, text="Entrar / Cadastrar", command=autenticar)
    botao_login.pack(pady=10)

    janelaLogin.mainloop()

# Inicia o programa
frmLogin()
conexao.close()
