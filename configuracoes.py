import os

CONFIG = {
    # Quantas vagas enviar por domínio por palavra-chave? (-1 = até o fim; 1 = uma vaga, etc.)
    "vagas_por_termo": 4,
    
    # Palavras-chave para pesquisar sequencialmente
    "palavras_chave": ["Python", "Desenvolvedor FullStack", "Cientista de Dados"],
    
    # Controle de Loop (0 = sem loop; -1 = infinito; 3 = faz o loop 3 vezes por toda a lista)
    "loops_sistema": 0,
    
    # Delay forçado (em segundos) entre cada ação no formulário para auditoria visual
    "delay_passo": 5,
    
   
    # Caminho do seu Currículo padrão para a validação visual do Tkinter
    "caminho_cv_padrao": os.path.abspath("CV-Data/CVs/CV - Marlon - DevFullStack.pdf"),
    
    "chrome_user_data_windows": os.path.abspath("PerfilAutomaçãoChrome"),
    "chrome_perfil_nome": "Default",

    # Filtros de Títulos de Vagas
    "titulos_aprovados": ["Python", "FullStack", "Cientista de Dados", "Testes", "QA", "Dados"],
    "titulos_desaprovados": ["Sênior", "Senior", "Sr", "Lead", "Gerente", "Diretor"],

    # Configurações de Comportamento
    "pausa_em_erro": True,
    "confirmacao_manual": False,

    # Caminho do Perfil do Arc Browser no Windows (Modificado para sua máquina)
    # "arc_user_data_windows": os.path.expandvars(r"%LocalAppData%\Arc\User Data")
}