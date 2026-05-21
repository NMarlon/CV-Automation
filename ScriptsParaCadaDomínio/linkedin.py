import os
import json
import time
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from interface_humana import InterfaceHumana

class LinkedInAutomator:
    def __init__(self, config_global):
        self.config = config_global
        self.interface = InterfaceHumana()
        self.dados_integracao = self._carregar_json("integracao.json").get("linkedin.com", {})
        self.respostas_db = self._carregar_json("respostas.json")
        self._inicializar_arquivos_log()

    def _inicializar_arquivos_log(self):
        if not os.path.exists("log.log"):
            with open("log.log", "w", encoding="utf-8") as f:
                f.write(f"=== SISTEMA DE LOGS INICIALIZADO EM {datetime.now()} ===\n")
        if not os.path.exists("log_estatisticas.csv"):
            with open("log_estatisticas.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["data_execucao", "titulo", "empresa", "link", "local", "modalidade", "postagem_bruta", "candidatos_bruto", "status", "erro"])

    def _carregar_json(self, caminho):
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except: return {}
        return {}

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def registrar_log(self, vaga_info, status, erro="", perguntas_respondidas=None):
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{agora}] ---------- VAGA PROCESSADA ----------\n")
            f.write(f"Título: {vaga_info.get('titulo')}\nEmpresa: {vaga_info.get('empresa')}\nLink: {vaga_info.get('link')}\nStatus: {status}\n")
            if erro: f.write(f"Erro: {erro}\n")
            f.write("-----------------------------------------\n")
        with open("log_estatisticas.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([agora, vaga_info.get('titulo'), vaga_info.get('empresa'), vaga_info.get('link'), vaga_info.get('local'), vaga_info.get('modalidade'), vaga_info.get('postagem'), vaga_info.get('candidatos'), status, erro])

    def tratar_excecao(self, link, passo, erro):
        print(f"⚠️ Falha no passo [{passo}]: {erro}")
        caminho_ajuste = "ListaAAjustar.json"
        lista_ajuste = self._carregar_json(caminho_ajuste)
        if not isinstance(lista_ajuste, list): lista_ajuste = []
        lista_ajuste.append({"url": link, "passo_falha": passo, "erro": str(erro), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        self._salvar_json(caminho_ajuste, lista_ajuste)

    def responder_fluxo_formulario(self, page, vaga_info):
        seletores = self.dados_integracao["seletores"]
        perguntas_da_sessao = {}
        
        while True:
            time.sleep(self.config.get("delay_passo", 2))
            
            # Captura fields no modal
            # No LinkedIn, campos costumam estar dentro de fieldsets ou divs com labels
            form_elements = page.query_selector_all(f"{seletores['modal_formulario']} .jobs-easy-apply-form-section__grouping")

            for element in form_elements:
                label_elem = element.query_selector("label")
                if not label_elem: continue

                texto_pergunta = label_elem.inner_text().strip()
                if not texto_pergunta: continue
                
                # Ignorar se já respondido nesta tela (prevenção de loop)
                if texto_pergunta in perguntas_da_sessao: continue

                chave_universal = self.respostas_db.get("perguntas_mapeadas", {}).get(texto_pergunta)
                resposta_final = None
                acao_usuario = None

                if chave_universal:
                    resposta_atual = self.respostas_db.get("valores_respostas", {}).get(chave_universal)
                    if self.config.get("confirmacao_manual"):
                        res_humana = self.interface.confirmar_campo(texto_pergunta, resposta_atual, chave_universal)
                        if res_humana["acao"] == "cancelar": raise Exception("Cancelado pelo usuário.")
                        resposta_final, acao_usuario = res_humana["resposta"], res_humana["acao"]
                    else:
                        resposta_final = resposta_atual
                else:
                    res_humana = self.interface.perguntar_resposta_nova(texto_pergunta)
                    if res_humana["acao"] == "cancelar": raise Exception("Cancelado pelo usuário.")
                    resposta_final, acao_usuario, chave_universal = res_humana["resposta"], res_humana["acao"], res_humana["chave"]

                if acao_usuario == "salvar_atualizar":
                    self.respostas_db.setdefault("perguntas_mapeadas", {})[texto_pergunta] = chave_universal
                    self.respostas_db.setdefault("valores_respostas", {})[chave_universal] = resposta_final
                    self._salvar_json("respostas.json", self.respostas_db)

                # Preenchimento
                input_elem = element.query_selector("input, select, textarea")
                if input_elem:
                    tag = input_elem.evaluate("el => el.tagName")
                    type_attr = input_elem.get_attribute("type")
                    
                    if tag == "SELECT":
                        input_elem.select_option(label=resposta_final)
                    elif type_attr == "radio":
                        # Encontra o rádio que corresponde à resposta
                        radios = element.query_selector_all("input[type='radio']")
                        for r in radios:
                            r_label = page.query_selector(f"label[for='{r.get_attribute('id')}']")
                            if r_label and resposta_final.lower() in r_label.inner_text().lower():
                                r.click()
                                break
                    elif type_attr == "checkbox":
                        if "sim" in resposta_final.lower() or "yes" in resposta_final.lower() or "aceito" in resposta_final.lower():
                            input_elem.check()
                    else:
                        input_elem.fill(resposta_final)
                
                perguntas_da_sessao[texto_pergunta] = resposta_final

            # Navegação
            btn_avancar = page.query_selector(seletores["botao_avancar_modal"])
            btn_revisar = page.query_selector(seletores["botao_revisar_modal"])
            btn_enviar = page.query_selector(seletores["botao_enviar_vaga"])
            
            if btn_avancar and btn_avancar.is_visible():
                btn_avancar.click()
            elif btn_revisar and btn_revisar.is_visible():
                btn_revisar.click()
            elif btn_enviar and btn_enviar.is_visible():
                # Verificação de CV
                if "currículo" in page.content().lower() or "cv" in page.content().lower():
                    res_anexo = self.interface.validar_anexo(self.config.get("caminho_cv_padrao"))
                    if res_anexo["acao"] == "cancelar": raise Exception("Envio cancelado no CV.")
                
                btn_enviar.click()
                time.sleep(3)
                if page.query_selector(seletores["confirmacao_sucesso"]):
                    self.registrar_log(vaga_info, "SUCESSO", perguntas_respondidas=perguntas_da_sessao)
                    page.keyboard.press("Escape")
                    return True
                raise Exception("Confirmação de sucesso não apareceu.")
            else:
                raise Exception("Nenhum botão de ação encontrado no modal.")

    def aplicar_vaga(self, page, url_vaga):
        seletores = self.dados_integracao["seletores"]
        vaga_info = {"link": url_vaga, "titulo": "N/A", "empresa": "N/A", "local": "N/A", "modalidade": "N/A", "postagem": "N/A", "candidatos": "N/A"}
        try:
            page.goto(url_vaga)
            page.wait_for_load_state("networkidle")
            for chave in ["titulo_vaga", "empresa_vaga", "local_vaga", "modalidade_vaga", "data_postagem", "num_candidatos"]:
                try:
                    el = page.locator(seletores.get(chave)).first
                    if el.is_visible(): vaga_info[chave.replace("_vaga", "").replace("num_", "").replace("data_", "")] = el.inner_text().strip()
                except: pass
            
            btn_candidatura = page.query_selector(seletores["botao_candidatura_simples"])
            if not btn_candidatura:
                self.registrar_log(vaga_info, "SKIP", "Não é Candidatura Simplificada")
                return False
                
            btn_candidatura.click()
            page.wait_for_selector(seletores["modal_formulario"])
            return self.responder_fluxo_formulario(page, vaga_info)
        except Exception as e:
            self.tratar_excecao(url_vaga, "Aplicação", e)
            self.registrar_log(vaga_info, "FALHA", str(e))
            return False

    def _garantir_login(self, page):
        page.goto("https://www.linkedin.com/feed/")
        if "feed" in page.url: return
        page.goto("https://www.linkedin.com/login")
        email, senha = self.config.get("email"), self.config.get("senha")
        if email and senha:
            page.fill("input#username", email)
            page.fill("input#password", senha)
            page.click('button[type="submit"]')
            try: page.wait_for_url("**/feed/**", timeout=10000)
            except: page.pause()
        else: page.pause()

    def executar_pesquisa(self, palavra_chave):
        user_data_dir = self.config.get("chrome_user_data_windows")
        perfil = self.config.get("chrome_perfil_nome", "Default")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(user_data_dir, headless=False, channel="chrome", args=[f"--profile-directory={perfil}", "--start-maximized"])
            page = context.pages[0] if context.pages else context.new_page()
            self._garantir_login(page)
            page.goto(self.dados_integracao["url_busca"].format(keyword=palavra_chave))
            page.wait_for_load_state("networkidle")
            
            seletor_lista = ".scaffold-layout__list"
            if page.query_selector(seletor_lista):
                for _ in range(3):
                    page.eval_on_selector(seletor_lista, "el => el.scrollTop += 800")
                    time.sleep(1)
            
            vagas_processadas, limite = 0, self.config.get("vagas_por_termo", -1)
            urls = []
            for item in page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"]):
                link_elem = item.query_selector(self.dados_integracao["seletores"]["card_vaga_link"])
                if link_elem:
                    href = link_elem.get_attribute("href")
                    if href:
                        url = href.split("?")[0]
                        if "jobs/view" in url and url not in urls: urls.append(url)

            for url in urls:
                if limite != -1 and vagas_processadas >= limite: break
                if self.aplicar_vaga(page, url): vagas_processadas += 1
                time.sleep(2)
            context.close()
