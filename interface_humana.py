import tkinter as tk
from tkinter import messagebox, ttk
import os
import subprocess

class InterfaceHumana:
    def __init__(self):
        pass

    def perguntar_resposta_nova(self, pergunta_texto, resposta_sugerida=""):
        """Abre uma janela para o usuário definir a chave universal e a resposta de uma nova pergunta encontrada."""
        root = tk.Tk()
        root.title("🤖 Pergunta Nova Encontrada!")
        root.attributes("-topmost", True)
        root.geometry("500x320")

        resultado = {"acao": "cancelar", "chave": "", "resposta": ""}

        # Labels e Campos
        tk.Label(root, text="O robô encontrou uma pergunta inédita:", font=("Arial", 10, "bold")).pack(pady=5)
        
        text_pergunta = tk.Text(root, height=3, width=55, wrap="word")
        text_pergunta.insert("1.0", pergunta_texto)
        text_pergunta.config(state="disabled")
        text_pergunta.pack(pady=5)

        tk.Label(root, text="Dê um ID/Chave Universal para esta pergunta (ex: exp_python):").pack(pady=2)
        entry_chave = tk.Entry(root, width=50)
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

        # Botões
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=15)

        tk.Button(frame_botoes, text="Enviar e Salvar no JSON", bg="#4CAF50", fg="white", command=salvar_atualizar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Enviar (Não Salvar)", bg="#FF9800", fg="white", command=enviar_sem_salvar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Pausar/Cancelar", bg="#f44336", fg="white", command=root.destroy).pack(side="left", padx=5)

        root.mainloop()
        return resultado

    def validar_anexo(self, caminho_arquivo):
        """Apresenta o anexo para validação visual antes do envio."""
        root = tk.Tk()
        root.title("📄 Confirmação de Anexo")
        root.attributes("-topmost", True)
        root.geometry("450x200")

        resultado = {"acao": "prosseguir"}
        nome_arquivo = os.path.basename(caminho_arquivo)

        tk.Label(root, text="O robô irá anexar o seguinte documento:", font=("Arial", 10, "bold")).pack(pady=10)
        tk.Label(root, text=nome_arquivo, fg="blue", font=("Arial", 10, "underline")).pack(pady=5)

        def visualizar():
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(caminho_arquivo)
                else:  # Mac / Linux
                    subprocess.run(['open' if os.name == 'mac' else 'xdg-open', caminho_arquivo])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o arquivo visualmente.\nErro: {e}")

        def confirmar():
            resultado["acao"] = "prosseguir"
            root.destroy()

        def trocar_arquivo():
            resultado["acao"] = "trocar"
            root.destroy()

        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=20)

        tk.Button(frame_botoes, text="👁️ Visualizar Arquivo", bg="#2196F3", fg="white", command=visualizar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="✅ Confirmar e Anexar", bg="#4CAF50", fg="white", command=confirmar).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="❌ Selecionar Outro", bg="#f44336", fg="white", command=trocar_arquivo).pack(side="left", padx=5)

        root.mainloop()
        return resultado