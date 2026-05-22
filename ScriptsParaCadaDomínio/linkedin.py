import os
import json
import time
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from interface_humana import InterfaceHumana

class LinkedInAutomator:
    def __init__(self, config_global):
        self.config = config_global
        # Carrega as variáveis do arquivo .env
        load_dotenv()
        self.username = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.interface = InterfaceHumana()
        self.dados_integracao = self._carregar_json("integracao.json")["linkedin.com"]
        self.respostas_db = self._carregar_json("respostas.json")
        self.fluxo_estados = self._carregar_json("fluxo_estados.json").get("linkedin.com", {})
        
        # GARANTE A CRIAÇÃO DOS ARQUIVOS DE LOG LOGO NO INÍCIO
        self._inicializar_arquivos_log()

    def _inicializar_arquivos_log(self):
        """Garante que os arquivos de log existam para mensurar o progresso desde o primeiro minuto"""
        if not os.path.exists("log.log"):
            with open("log.log", "w", encoding="utf-8") as f:
                f.write(f"=== SISTEMA DE LOGS INICIALIZADO EM {datetime.now()} ===\n")
                
        if not os.path.exists("log_estatisticas.csv"):
            with open("log_estatisticas.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["data_execucao", "titulo", "empresa", "link", "local", "modalidade", "postagem_bruta", "candidatos_bruto", "status", "erro", "titulo_pulado"])
    def _carregar_json(self, caminho):
        
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def registrar_log(self, vaga_info, status, erro="", perguntas_respondidas=None, titulo_pulado=False):
        """Gera logs legíveis no log.log e tabulares no log_estatisticas.csv"""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Log textual legível
        with open("log.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{agora}] ---------- VAGA PROCESSADA ----------\n")
            f.write(f"Título: {vaga_info.get('titulo')}\nEmpresa: {vaga_info.get('empresa')}\n")
            f.write(f"Link: {vaga_info.get('link')}\nStatus: {status}\n")
            if titulo_pulado: f.write("Motivo: Título não aprovado ou desaprovado.\n")
            if erro: f.write(f"Erro encontrado: {erro}\n")
            if perguntas_respondidas: f.write(f"Perguntas respondidas: {json.dumps(perguntas_respondidas)}\n")
            f.write("-----------------------------------------\n")

        # 2. Log em CSV para processamento estatístico posterior
        csv_existe = os.path.exists("log_estatisticas.csv")
        with open("log_estatisticas.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not csv_existe:
                writer.writerow(["data_execucao", "titulo", "empresa", "link", "local", "modalidade", "postagem_bruta", "candidatos_bruto", "status", "erro", "titulo_pulado"])
            writer.writerow([
                agora, vaga_info.get('titulo'), vaga_info.get('empresa'), vaga_info.get('link'),
                vaga_info.get('local'), vaga_info.get('modalidade'), vaga_info.get('postagem'),
                vaga_info.get('candidatos'), status, erro, "Sim" if titulo_pulado else "Não"
            ])

    def tratar_excecao(self, link, passo, erro):
        """Trata falhas salvando o progresso na Lista a Ajustar"""
        print(f"⚠️ Falha no passo [{passo}]: {erro}. Salvando na ListaAAjustar.")
        lista_ajuste = self._carregar_json("lista_a_ajustar.json")
        if not isinstance(lista_ajuste, list): lista_ajuste = []
        
        lista_ajuste.append({
            "url": link,
            "passo_falha": passo,
            "erro": str(erro),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._salvar_json("lista_a_ajustar.json", lista_ajuste)

    def responder_fluxo_formulario(self, page, vaga_info):
        """Gerencia as etapas internas do Modal de Candidatura Simplificada"""
        seletores = self.dados_integracao["seletores"]
        perguntas_da_sessao = {}
        
        while True:
            # Forçar o delay configurado para permitir auditoria visual ou Pausa
            time.sleep(self.config.get("delay_passo", 0))
            
            # Identificar Inputs de texto, Radio Buttons ou Selects na tela atual do Modal
            # Varre os elementos visíveis para capturar perguntas
            labels = page.query_selector_all(f"{seletores['modal_formulario']} label")
            for label in labels:
                texto_pergunta = label.inner_text().strip()
                if not texto_pergunta: continue
                
                # Verifica se já conhecemos a pergunta
                chave_universal = self.respostas_db.get("perguntas_mapeadas", {}).get(texto_pergunta)
                
                if chave_universal:
                    resposta_final = self.respostas_db.get("valores_respostas", {}).get(chave_universal)
                else:
                    # Pergunta inédita identificada -> Aciona Tkinter
                    print(f"❓ Pergunta inédita: '{texto_pergunta}'")
                    res_humana = self.interface.perguntar_resposta_nova(texto_pergunta)
                    
                    if res_humana["acao"] == "cancelar":
                        raise Exception("Execução cancelada pelo usuário na tela de perguntas.")
                        
                    resposta_final = res_humana["resposta"]
                    
                    if res_humana["acao"] == "salvar_atualizar":
                        # Atualiza base de dados JSON persistentemente
                        self.respostas_db.setdefault("perguntas_mapeadas", {})[texto_pergunta] = res_humana["chave"]
                        self.respostas_db.setdefault("valores_respostas", {})[res_humana["chave"]] = resposta_final
                        self._salvar_json("respostas.json", self.respostas_db)
                
                # Preencher o campo com base no elemento associado ao label
                id_alvo = label.get_attribute("for")
                if id_alvo:
                    campo = page.query_selector(f"#{id_alvo}")
                    if campo:
                        tag_name = campo.evaluate("el => el.tagName")
                        if tag_name == "INPUT":
                            campo.fill(resposta_final)
                        elif tag_name == "SELECT":
                            campo.select_option(label=resposta_final)
                
                perguntas_da_sessao[texto_pergunta] = resposta_final

            # Lógica de Avanço de Etapas
            btn_avancar = page.query_selector(seletores["botao_avancar_modal"])
            btn_revisar = page.query_selector(seletores["botao_revisar_modal"])
            btn_enviar = page.query_selector(seletores["botao_enviar_vaga"])
            
            if btn_avancar and btn_avancar.is_visible():
                btn_avancar.click()
            elif btn_revisar and btn_revisar.is_visible():
                btn_revisar.click()
            elif btn_enviar and btn_enviar.is_visible():
                # Tratamento de confirmação de anexo se houver área de upload visível
                if "currículo" in page.content().lower() or "cv" in page.content().lower():
                    # Simula a checagem do documento padrão configurado
                    checar_cv = self.interface.validar_anexo(self.config.get("caminho_cv_padrao", "cv.pdf"))
                    if checar_cv["acao"] == "cancelar":
                        raise Exception("Envio cancelado na verificação do currículo.")
                
                btn_enviar.click()
                time.sleep(3) # Aguarda renderização da tela de sucesso
                
                # Confirmação Real de Conclusão por Seletor de Sucesso
                if page.query_selector(seletores["confirmacao_sucesso"]):
                    print("🎉 Candidatura enviada com sucesso!")
                    self.registrar_log(vaga_info, "SUCESSO", perguntas_respondidas=perguntas_da_sessao)
                    # Fechar modal de sucesso se aplicável
                    page.keyboard.press("Escape")
                    return True
                else:
                    raise Exception("Botão de enviar clicado, mas tela de confirmação não apareceu.")
            else:
                raise Exception("Modal estagnado. Nenhum botão de avanço ou envio encontrado.")

    def detectar_estado_atual(self, page):
        """Identifica em qual estágio da navegação a página se encontra"""
        url_atual = page.url
        print(f"🕵️ Detectando estado atual... (URL: {url_atual})")

        estados = self.fluxo_estados.get("ESTADOS", {})

        # Ordem de prioridade na detecção
        for nome_estado, config in estados.items():
            # Se houver seletor chave e ele estiver visível, esse é o estado
            if config.get("seletor_chave"):
                try:
                    if page.is_visible(config["seletor_chave"], timeout=2000):
                        return nome_estado
                except:
                    pass

            # Se a URL contém o padrão definido
            if config.get("url_contem") and config["url_contem"] in url_atual:
                return nome_estado

        return "DESCONHECIDO"

    def aplicar_vaga(self, page, url_vaga):
        """Processa uma vaga individual do início ao fim"""
        seletores = self.dados_integracao["seletores"]
        vaga_info = {"link": url_vaga}
        
        try:
            print(f"🔗 Abrindo vaga: {url_vaga}")
            page.goto(url_vaga)
            page.wait_for_load_state("networkidle")
            
            # Extração de Dados Ricos para Estatísticas
            try:
                vaga_info["titulo"] = page.locator(seletores["titulo_vaga"]).inner_text().strip()
                vaga_info["empresa"] = page.locator(seletores["empresa_vaga"]).inner_text().strip()
                vaga_info["local"] = page.locator(seletores["local_vaga"]).inner_text().strip()
                vaga_info["modalidade"] = page.locator(seletores["modalidade_vaga"]).inner_text().strip()
                vaga_info["postagem"] = page.locator(seletores["data_postagem"]).inner_text().strip()
                vaga_info["candidatos"] = page.locator(seletores["num_candidatos"]).inner_text().strip()
            except Exception:
                # Fallback parcial se algum metadado falhar, para não travar a candidatura
                pass

            # Checa se possui o botão de Candidatura Simplificada
            btn_candidatura = page.query_selector(seletores["botao_candidatura_simples"])
            if not btn_candidatura:
                print("⏭️ Vaga não possui Candidatura Simplificada. Pulando.")
                self.registrar_log(vaga_info, "SKIP", "Não possui Candidatura Simplificada")
                return False
                
            print("🚀 Iniciando Candidatura Simplificada...")
            btn_candidatura.click()
            page.wait_for_selector(seletores["modal_formulario"])
            
            # Entra no preenchimento dinâmico por etapas
            return self.responder_fluxo_formulario(page, vaga_info)
            
        except Exception as e:
            self.tratar_excecao(url_vaga, "Processando Formulário/Envio", e)
            self.registrar_log(vaga_info, "FALHA", str(e))
            return False

    def _garantir_login(self, page):
        """Verifica a autenticação e tenta logar se necessário."""
        print("🔒 Verificando estado da autenticação...")
        
        estado = self.detectar_estado_atual(page)

        if estado in ["FEED", "BUSCA_VAGAS", "DETALHE_VAGA", "MODAL_CANDIDATURA"]:
            print(f"✅ Usuário já autenticado (Estado: {estado}).")
            return

        print("🔑 Sessão não encontrada ou em tela de login. Iniciando login...")
        
        try:
            if estado != "LOGIN":
                # Força ir para a página de login dedicada (é mais estável que a Landing Page)
                page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            # Re-detectar se caiu no login mesmo
            if not page.is_visible("input#username", timeout=5000):
                estado_pos_goto = self.detectar_estado_atual(page)
                if estado_pos_goto in ["FEED", "BUSCA_VAGAS", "DETALHE_VAGA"]:
                    print("✅ Já estava logado após o redirecionamento.")
                    return

            # Preenchendo o E-mail
            if page.is_visible("input#username"):
                page.fill("input#username", self.username or "seu_email@gmail.com")
            elif page.is_visible('input[name="session_key"]'):
                page.fill('input[name="session_key"]', self.username or "seu_email@gmail.com")
            else:
                print("⚠️ Campo de e-mail não identificado. Verifique se já está logado ou se a página mudou.")
                # Se não viu o e-mail, pode ser que já logou por cookie/perfil persistente
                if self.detectar_estado_atual(page) != "LOGIN":
                    return

            # Preenchendo a Senha
            if page.is_visible("input#password"):
                page.fill("input#password", self.password or "sua_senha_secreta")
            elif page.is_visible('input[name="session_password"]'):
                page.fill('input[name="session_password"]', self.password or "sua_senha_secreta")

            # Clicando no Botão de Entrar
            botao_entrar = page.locator('button[type="submit"]')
            if botao_entrar.is_visible():
                botao_entrar.click()
            else:
                page.press("input#password", "Enter")

            # Espera o redirecionamento para o Feed (ou pede intervenção se aparecer Captcha)
            try:
                page.wait_for_url("**/feed/**", timeout=15000)
                print("🎉 Login efetuado com sucesso!")
            except:
                # Se der timeout no feed, pode ser que redirecionou para outra página válida
                if self.detectar_estado_atual(page) != "LOGIN":
                    print("🎉 Login parece ter tido sucesso (não está mais na tela de login).")
                else:
                    raise Exception("Ainda na tela de login após tentativa.")

        except Exception as e:
            print(f"\n❌ Erro durante o processo de login: {e}")
            if self.config.get("pausa_em_erro"):
                print("🛑 Entrando em modo de pausa para inspeção. Analise o navegador aberto!")
                page.pause()
            
            raise Exception("Falha no login: O robô não conseguiu acessar a página inicial após a tentativa de autenticação.")




    def registrar_progresso(self, termo, url_vaga=None):
        """Salva o progresso atual para retomada em caso de falha"""
        progresso = {
            "termo": termo,
            "url_vaga": url_vaga,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._salvar_json("progresso.json", progresso)

    def executar_pesquisa(self, palavra_chave):
        """Inicia a sessão do Playwright acoplada ao Chrome Browser para rodar a busca"""
        print(f"🔍 Iniciando busca por '{palavra_chave}' no LinkedIn...")
        
        with open("log.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando pesquisa pelo termo: '{palavra_chave}'\n")
            
        user_data_dir = self.config.get("chrome_user_data_windows")
        perfil_nome = self.config.get("chrome_perfil_nome", "Default")
        
        with sync_playwright() as p:
            print("🌐 Abrindo o Google Chrome...")
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                channel="chrome", 
                args=[
                    f"--profile-directory={perfil_nome}",
                    "--disable-extensions",
                    "--start-maximized"
                ]
            )
            
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()
                
            # EXECUTA A CAMADA INTELIGENTE DE LOGIN ANTES DE IR PARA A BUSCA
            self._garantir_login(page)
                
            url_busca = self.dados_integracao["url_busca"].format(keyword=palavra_chave)
            print(f"✈️ Navegando para a busca do LinkedIn...")
            page.goto(url_busca)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(4)
            
            # --- Scroll na lista lateral ---
            seletor_lista = ".scaffold-layout__list"
            if page.query_selector(seletor_lista):
                print("📜 Rolando a lista de vagas para carregar dados do LinkedIn...")
                for _ in range(3):
                    page.eval_on_selector(seletor_lista, "el => el.scrollTop += 600")
                    time.sleep(1)
            # --------------------------------------------------------
            
            vagas_processadas = 0
            limite_vagas = self.config.get("vagas_por_termo", -1)
            
            # Varredura das vagas da barra lateral esquerda
            lista_itens = page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"])
            vagas_extraidas = []

            progresso = self._carregar_json("progresso.json")
            url_retomada = progresso.get("url_vaga") if progresso else None
            
            for item in lista_itens:
                link_elem = item.query_selector(self.dados_integracao["seletores"]["card_vaga_link"])
                titulo_elem = item.query_selector(self.dados_integracao["seletores"]["titulo_vaga_card"])

                if link_elem:
                    href = link_elem.get_attribute("href")
                    url_limpa = href.split("?")[0] if href else ""
                    titulo = titulo_elem.inner_text().strip() if titulo_elem else "Título não encontrado"

                    if url_limpa:
                        vagas_extraidas.append({
                            "url": url_limpa,
                            "titulo": titulo
                        })

            if not vagas_extraidas:
                print("🏁 Nenhuma vaga encontrada na página.")
                with open("log.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🏁 Nenhuma vaga encontrada para o termo '{palavra_chave}'.\n")
            else:
                print(f"📦 Encontradas {len(vagas_extraidas)} vagas nesta página.")
                with open("log.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Encontradas {len(vagas_extraidas)} vagas para o termo '{palavra_chave}'.\n")

            if url_retomada:
                # Filtra a lista para começar após a última vaga tentada
                urls = [v["url"] for v in vagas_extraidas]
                if url_retomada in urls:
                    indice = urls.index(url_retomada)
                    print(f"⏩ Retomando lista de vagas a partir de: {url_retomada}")
                    vagas_extraidas = vagas_extraidas[indice:]

            for vaga in vagas_extraidas:
                if limite_vagas != -1 and vagas_processadas >= limite_vagas:
                    print("🛑 Limite de vagas atingido para esta palavra-chave.")
                    break
                
                url = vaga["url"]
                titulo = vaga["titulo"]

                self.registrar_progresso(palavra_chave, url)

                # --- Lógica de Filtro de Título ---
                titulos_aprovados = self.config.get("titulos_aprovados", [])
                titulos_desaprovados = self.config.get("titulos_desaprovados", [])

                aprovado = True
                if titulos_aprovados:
                    aprovado = any(keyword.lower() in titulo.lower() for keyword in titulos_aprovados)

                desaprovado = False
                if titulos_desaprovados:
                    desaprovado = any(keyword.lower() in titulo.lower() for keyword in titulos_desaprovados)

                if not aprovado or desaprovado:
                    print(f"⏩ Pulando vaga por filtro de título: {titulo}")
                    self.registrar_log({"titulo": titulo, "link": url}, "titulo_pulado", titulo_pulado=True)
                    continue

                sucesso = self.aplicar_vaga(page, url)
                if sucesso:
                    vagas_processadas += 1
                
                time.sleep(2)

            # Limpa progresso ao finalizar termo
            if os.path.exists("progresso.json"):
                os.remove("progresso.json")

            context.close()
            print(f"🏁 Concluída pesquisa do termo '{palavra_chave}' no LinkedIn.")