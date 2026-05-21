import os

CONFIG = {
    # Quantas vagas enviar por domínio por palavra-chave? (-1 = até o fim; 1 = uma vaga, etc.)
    "vagas_por_termo": 4,
    
    # Palavras-chave para pesquisar sequencialmente
    "palavras_chave": ["Python", "Desenvolvedor FullStack", "Cientista de Dados"],
    
    # Controle de Loop (0 = sem loop; -1 = infinito; 3 = faz o loop 3 vezes por toda a lista)
    "loops_sistema": 0,
    
    # SE o sistema deve pedir confirmação manual para cada campo/pergunta
    "confirmacao_manual": True,

    # Delay forçado (em segundos) entre cada ação no formulário para auditoria visual
    "delay_passo": 2,
    
    # Caminho do seu Currículo padrão
    "caminho_cv_padrao": os.path.abspath("CV-Data/CVs/CV - Marlon - DevFullStack.pdf"),
    
    # Configurações do Navegador
    "chrome_user_data_windows": os.path.abspath("PerfilAutomaçãoChrome"),
    "chrome_perfil_nome": "Default",

    # E-mail e Senha para login automático (Opcional se usar perfil persistente logado)
    "email": "seu_email@gmail.com",
    "senha": "sua_senha_secreta"
}
