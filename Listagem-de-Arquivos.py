import os

def gerar_relatorio_diretorio(caminho_base='.', arquivo_saida='lista_arquivos.txt', pastas_ignoradas=None):
    """
    Gera um relatório textual da estrutura de pastas e arquivos,
    com opção de ignorar pastas específicas (e suas subpastas).
    
    :param caminho_base: Diretório onde o escaneamento vai começar.
    :param arquivo_saida: Nome ou caminho do arquivo de texto gerado.
    :param pastas_ignoradas: Lista de nomes de pastas que não devem ser exploradas.
    """
    if pastas_ignoradas is None:
        pastas_ignoradas = []
        
    # Normalizamos para evitar problemas com letras maiúsculas/minúsculas
    pastas_ignoradas = [p.lower() for p in pastas_ignoradas]
    
    # Pegamos o caminho absoluto do arquivo de saída para evitar que ele se auto-liste
    caminho_absoluto_saida = os.path.abspath(arquivo_saida)

    try:
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            f.write(f"Relatório de estrutura: {os.path.abspath(caminho_base)}\n")
            f.write("="*50 + "\n\n")

            # os.walk percorre a pasta, subpastas e arquivos
            for raiz, diretorios, arquivos in os.walk(caminho_base):
                
                # --- LÓGICA DE EXCLUSÃO ---
                # Modificar a lista 'diretorios' in-place impede o os.walk de descer nessas pastas
                # Consequentemente, ignora todas as subpastas delas automaticamente
                diretorios[:] = [d for d in diretorios if d.lower() not in pastas_ignoradas]
                
                # Escreve o nome da pasta atual
                f.write(f"\n[DIRETÓRIO] {raiz}\n")
                
                # Escreve os arquivos encontrados nessa pasta
                for nome_arquivo in arquivos:
                    caminho_completo_arquivo = os.path.abspath(os.path.join(raiz, nome_arquivo))
                    
                    # Verificação de segurança: Não listar o próprio arquivo de relatório
                    if caminho_completo_arquivo != caminho_absoluto_saida:
                        f.write(f"  ├── {nome_arquivo}\n")
        
        print(f"Relatório gerado com sucesso em: {arquivo_saida}")
        if pastas_ignoradas:
            print(f"Pastas e subpastas ignoradas: {', '.join(pastas_ignoradas)}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")


# --- CONFIGURAÇÃO ---
diretorio_alvo = '.'
nome_relatorio = 'lista_arquivos.txt'

# Adicione aqui as pastas que você quer que o script pule completamente
pastas_para_pular = ['.git', '__pycache__', 'Cenários','.venv', '.obsidian', 'Archive', '.venv', 'Para os Bots']

# Executa a função passando o array de ignorados
gerar_relatorio_diretorio(
    caminho_base=diretorio_alvo, 
    arquivo_saida=nome_relatorio, 
    pastas_ignoradas=pastas_para_pular
)