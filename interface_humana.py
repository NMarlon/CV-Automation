import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import subprocess

class InterfaceHumana:
    def __init__(self):
        pass

    def perguntar_resposta_nova(self, pergunta_texto, resposta_sugerida="", chave_sugerida=""):
        """Abre uma janela para o usuário definir a chave universal e a resposta de uma nova pergunta encontrada."""
        root = tk.Tk()
        root.title("🤖 Pergunta Nova Encontrada!")
        root.attributes("-topmost", True)
        root.geometry("550x400")

        resultado = {"acao": "cancelar", "chave": "", "resposta": ""}

        # Labels e Campos
        tk.Label(root, text="O robô encontrou uma pergunta inédita:", font=("Arial", 10, "bold")).pack(pady=5)
        
        text_pergunta = tk.Text(root, height=4, width=60, wrap="word")
        text_pergunta.insert("1.0", pergunta_texto)
        text_pergunta.config(state="disabled")
        text_pergunta.pack(pady=5)

        tk.Label(root, text="Dê um ID/Chave Universal para esta pergunta (ex: exp_python):").pack(pady=2)
        entry_chave = tk.Entry(root, width=50)
        entry_chave.insert(0, chave_sugerida)
        entry_chave.pack(pady=2)

        tk.Label(root, text="Digite a Resposta a ser enviada:").pack(pady=2)
        entry_resposta = tk.Entry(root, width=50)
        entry_resposta.insert(0, resposta_sugerida)
        entry_resposta.pack(pady=2)

        def salvar_atualizar():
            resultado["acao"] = "salvar_atualizar"
            resultado["chave"] = entry_chave.get().strip()
            resultado["resposta"] = entry_resposta.get().strip()
            root.destroy()

        def enviar_sem_salvar():
            resultado["acao"] = "enviar_nao_salvar"
            resultado["resposta"] = entry_resposta.get().strip()
            root.destroy()

        def cancelar():
            resultado["acao"] = "cancelar"
            root.destroy()

        # Botões
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=15)

        tk.Button(frame_botoes, text="Enviar e Salvar no JSON", bg="#4CAF50", fg="white", command=salvar_atualizar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Enviar (Não Salvar)", bg="#FF9800", fg="white", command=enviar_sem_salvar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Pausar/Cancelar", bg="#f44336", fg="white", command=cancelar).pack(side="left", padx=5)

        root.mainloop()
        return resultado

    def confirmar_campo(self, pergunta_texto, resposta_atual, chave_universal):
        """Abre uma janela para confirmar ou editar uma resposta já conhecida."""
        root = tk.Tk()
        root.title("🔎 Confirmar Resposta")
        root.attributes("-topmost", True)
        root.geometry("550x350")

        resultado = {"acao": "cancelar", "resposta": ""}

        tk.Label(root, text="Pergunta:", font=("Arial", 10, "bold")).pack(pady=5)
        text_pergunta = tk.Text(root, height=3, width=60, wrap="word")
        text_pergunta.insert("1.0", pergunta_texto)
        text_pergunta.config(state="disabled")
        text_pergunta.pack(pady=5)

        tk.Label(root, text=f"Chave: {chave_universal}", font=("Arial", 8, "italic")).pack()

        tk.Label(root, text="Resposta sugerida (edite se necessário):").pack(pady=5)
        entry_resposta = tk.Entry(root, width=50)
        entry_resposta.insert(0, resposta_atual)
        entry_resposta.pack(pady=5)

        def salvar_atualizar():
            resultado["acao"] = "salvar_atualizar"
            resultado["resposta"] = entry_resposta.get().strip()
            root.destroy()

        def enviar_sem_salvar():
            resultado["acao"] = "enviar_nao_salvar"
            resultado["resposta"] = entry_resposta.get().strip()
            root.destroy()

        def cancelar():
            resultado["acao"] = "cancelar"
            root.destroy()

        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=15)

        tk.Button(frame_botoes, text="Enviar e Atualizar JSON", bg="#4CAF50", fg="white", command=salvar_atualizar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Enviar (Não Salvar)", bg="#FF9800", fg="white", command=enviar_sem_salvar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Pausar/Cancelar", bg="#f44336", fg="white", command=cancelar).pack(side="left", padx=5)

        root.mainloop()
        return resultado

    def validar_anexo(self, caminho_arquivo):
        """Apresenta o anexo para validação visual antes do envio."""
        root = tk.Tk()
        root.title("📄 Confirmação de Anexo")
        root.attributes("-topmost", True)
        root.geometry("500x250")

        resultado = {"acao": "cancelar", "caminho": caminho_arquivo}

        tk.Label(root, text="O robô irá anexar o seguinte documento:", font=("Arial", 10, "bold")).pack(pady=10)
        label_nome = tk.Label(root, text=os.path.basename(resultado["caminho"]), fg="blue", font=("Arial", 10, "underline"))
        label_nome.pack(pady=5)

        def visualizar():
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(resultado["caminho"])
                else:  # Mac / Linux
                    subprocess.run(['open' if os.name == 'mac' else 'xdg-open', resultado["caminho"]])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o arquivo visualmente.\nErro: {e}")

        def confirmar():
            resultado["acao"] = "prosseguir"
            root.destroy()

        def trocar_arquivo():
            novo_caminho = filedialog.askopenfilename(title="Selecionar Currículo", filetypes=[("Documentos", "*.pdf *.docx *.txt"), ("Todos os arquivos", "*.*")])
            if novo_caminho:
                resultado["caminho"] = novo_caminho
                label_nome.config(text=os.path.basename(novo_caminho))

        def cancelar():
            resultado["acao"] = "cancelar"
            root.destroy()

        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=20)

        tk.Button(frame_botoes, text="👁️ Visualizar", bg="#2196F3", fg="white", command=visualizar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="✅ Enviar e Atualizar", bg="#4CAF50", fg="white", command=confirmar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="📂 Selecionar Outro", bg="#607D8B", fg="white", command=trocar_arquivo).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="❌ Cancelar", bg="#f44336", fg="white", command=cancelar).pack(side="left", padx=5)

        root.mainloop()
        return resultado
