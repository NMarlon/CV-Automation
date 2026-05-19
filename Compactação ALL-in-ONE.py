import os

def consolidar_arquivos(diretorio_raiz, arquivo_saida, extensoes_permitidas, incluir_subpastas=True, pastas_ignoradas=None, arquivos_ignorados=None):
    """
    Consolida arquivos com base em uma lista de extensões permitidas,
    com opção de ignorar pastas e arquivos específicos.
    
    :param arquivo_saida: Nome ou caminho do arquivo final gerado.
    :param extensoes_permitidas: Lista/Array de extensões (ex: ['py', 'md', 'txt']).
    :param incluir_subpastas: True para recursivo, False para apenas a raiz.
    :param pastas_ignoradas: Lista de nomes de pastas que não devem ser exploradas.
    :param arquivos_ignorados: Lista de nomes de arquivos específicos a serem pulados (ex: ['.env', 'ignorado.txt']).
    """
    if pastas_ignoradas is None:
        pastas_ignoradas = []
    if arquivos_ignorados is None:
        arquivos_ignorados = []
    
    # Normalizamos pastas, extensões e arquivos para evitar problemas com maiúsculas/minúsculas
    pastas_ignoradas = [p.lower() for p in pastas_ignoradas]
    arquivos_ignorados = [a.lower() for a in arquivos_ignorados]
    extensoes_permitidas = [ext.lower().lstrip('.') for ext in extensoes_permitidas]

    # Pegamos o caminho absoluto do arquivo de saída para a verificação de segurança
    caminho_absoluto_saida = os.path.abspath(arquivo_saida)

    with open(arquivo_saida, 'w', encoding='utf-8') as outfile:
        
        if incluir_subpastas:
            gerador_arquivos = os.walk(diretorio_raiz)
        else:
            arquivos_locais = [f.name for f in os.scandir(diretorio_raiz) if f.is_file()]
            gerador_arquivos = [(diretorio_raiz, [], arquivos_locais)]

        for raiz, dirs, arquivos in gerador_arquivos:
            
            # --- LÓGICA DE EXCLUSÃO DE PASTAS ---
            dirs[:] = [d for d in dirs if d.lower() not in pastas_ignoradas]
            
            for nome_arquivo in arquivos:
                caminho_completo = os.path.abspath(os.path.join(raiz, nome_arquivo))
                nome_arquivo_lower = nome_arquivo.lower()
                
                # 1. Verificação de Arquivos Ignorados
                if nome_arquivo_lower in arquivos_ignorados:
                    continue  # Pula direto para o próximo arquivo da lista
                
                # 2. Verificação de Extensão Dinâmica
                _, ext = os.path.splitext(nome_arquivo)
                is_extensao_valida = ext.lower().lstrip('.') in extensoes_permitidas
                
                # 3. Verificação de Segurança Robusta (Evita ler o próprio arquivo de saída)
                is_nao_saida = caminho_completo != caminho_absoluto_saida
                
                if is_extensao_valida and is_nao_saida:
                    titulo = os.path.splitext(nome_arquivo)[0]
                    
                    try:
                        with open(caminho_completo, 'r', encoding='utf-8') as infile:
                            conteudo = infile.read()
                            
                            outfile.write("---\n---\n---\n")
                            outfile.write(f"# Arquivo: {nome_arquivo}\n")
                            outfile.write(f"Diretório: {caminho_completo}\n")
                            outfile.write(f"Título: {titulo}\n\n")
                            outfile.write(conteudo)
                            outfile.write("\n\n") 
                            
                    except Exception as e:
                        print(f"Erro ao ler {nome_arquivo}: {e}")

    print(f"Sucesso! Consolidação concluída em: {arquivo_saida}")
    print(f"Modo: {'Recursivo' if incluir_subpastas else 'Apenas Raiz'}")
    print(f"Extensões processadas: {', '.join(extensoes_permitidas)}")
    if arquivos_ignorados:
        print(f"Arquivos ignorados: {', '.join(arquivos_ignorados)}")


# --- CONFIGURAÇÃO ---
diretorio_alvo = '.' 
nome_resultado = 'Consolidado-CV-Auto.md'

formatos_validos = ['py', 'md', 'txt', 'json', 'log.log','.gitignore']
quero_subpastas = True 
pastas_para_pular = ['.git', '__pycache__', 'venv', 'Cenários', '.obsidian', 'Archive', '.venv', 'Para os Bots'] 

# NOVA CHAVE DE CONTROLE:
# Adicione aqui os nomes exatos dos arquivos que deseja ignorar
arquivos_para_pular = ['.env']

# Chamada da função atualizada
consolidar_arquivos(
    diretorio_raiz=diretorio_alvo, 
    arquivo_saida=nome_resultado, 
    extensoes_permitidas=formatos_validos,
    incluir_subpastas=quero_subpastas, 
    pastas_ignoradas=pastas_para_pular,
    arquivos_ignorados=arquivos_para_pular
)