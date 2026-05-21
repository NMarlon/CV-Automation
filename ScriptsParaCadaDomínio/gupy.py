import os
import json
import time
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from interface_humana import InterfaceHumana

class GupyAutomator:
    def __init__(self, config_global):
        self.config = config_global
        self.interface = InterfaceHumana()
        self.dados_integracao = self._carregar_json("integracao.json").get("gupy.io", {})
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
            f.write(f"\n[{agora}] ---------- VAGA GUPY ----------\n")
            f.write(f"Título: {vaga_info.get('titulo')}\nEmpresa: {vaga_info.get('empresa')}\nStatus: {status}\n")
            f.write("-----------------------------------------\n")
        with open("log_estatisticas.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([agora, vaga_info.get('titulo'), vaga_info.get('empresa'), vaga_info.get('link'), vaga_info.get('local'), vaga_info.get('modalidade'), vaga_info.get('postagem'), vaga_info.get('candidatos'), status, erro])

    def tratar_excecao(self, link, passo, erro):
        caminho_ajuste = "ListaAAjustar.json"
        lista_ajuste = self._carregar_json(caminho_ajuste)
        if not isinstance(lista_ajuste, list): lista_ajuste = []
        lista_ajuste.append({"url": link, "passo_falha": passo, "erro": str(erro), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        self._salvar_json(caminho_ajuste, lista_ajuste)

    def responder_fluxo_formulario(self, page, vaga_info):
        seletores = self.dados_integracao["seletores"]
        try:
            # Gupy formulário é dinâmico e muitas vezes multi-step
            while True:
                time.sleep(self.config.get("delay_passo", 2))

                # Procura por campos de input/select/radio
                fields = page.query_selector_all("div[class*='Question_container']")
                for field in fields:
                    label_elem = field.query_selector("label") or field.query_selector("p[class*='Question_title']")
                    if not label_elem: continue

                    texto_pergunta = label_elem.inner_text().strip()
                    if not texto_pergunta: continue

                    # Lógica de resposta (similar ao LinkedIn)
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

                    # Preencher o campo no Gupy
                    input_field = field.query_selector("input, textarea, select")
                    if input_field:
                        tag = input_field.evaluate("el => el.tagName")
                        if tag == "SELECT":
                            input_field.select_option(label=resposta_final)
                        elif input_field.get_attribute("type") == "radio":
                            radios = field.query_selector_all("label")
                            for r in radios:
                                if resposta_final.lower() in r.inner_text().lower():
                                    r.click()
                                    break
                        else:
                            input_field.fill(resposta_final)

                btn_proximo = page.query_selector(seletores["botao_avancar_modal"])
                btn_enviar = page.query_selector(seletores["botao_enviar_vaga"])

                if btn_enviar and btn_enviar.is_visible():
                    btn_enviar.click()
                    time.sleep(3)
                    if page.query_selector(seletores["confirmacao_sucesso"]):
                        self.registrar_log(vaga_info, "SUCESSO")
                        return True
                    break
                elif btn_proximo and btn_proximo.is_visible():
                    btn_proximo.click()
                else:
                    break
            return False
        except Exception as e:
            self.tratar_excecao(vaga_info["link"], "Gupy Flow", e)
            return False

    def aplicar_vaga(self, page, url_vaga):
        seletores = self.dados_integracao["seletores"]
        vaga_info = {"link": url_vaga, "titulo": "Gupy Job", "empresa": "N/A", "local": "N/A", "modalidade": "N/A", "postagem": "N/A", "candidatos": "N/A"}
        try:
            page.goto(url_vaga)
            page.wait_for_load_state("networkidle")

            # Extrair infos básicas
            try:
                vaga_info["titulo"] = page.locator(seletores["titulo_vaga"]).inner_text().strip()
                vaga_info["empresa"] = page.locator(seletores["empresa_vaga"]).inner_text().strip()
            except: pass

            btn_candidatura = page.query_selector(seletores["botao_candidatura_simples"])
            if btn_candidatura:
                btn_candidatura.click()
                time.sleep(2)
                if "login" in page.url:
                    print("🔑 Gupy: Necessário login.")
                    page.pause()
                return self.responder_fluxo_formulario(page, vaga_info)
            return False
        except Exception as e:
            self.tratar_excecao(url_vaga, "Gupy Aplicação", e)
            return False

    def executar_pesquisa(self, palavra_chave):
        user_data_dir = self.config.get("chrome_user_data_windows")
        perfil = self.config.get("chrome_perfil_nome", "Default")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(user_data_dir, headless=False, channel="chrome", args=[f"--profile-directory={perfil}", "--start-maximized"])
            page = context.pages[0] if context.pages else context.new_page()

            url_busca = self.dados_integracao["url_busca"].format(keyword=palavra_chave)
            page.goto(url_busca)
            page.wait_for_load_state("networkidle")

            vagas_processadas, limite = 0, self.config.get("vagas_por_termo", -1)

            # Scroll e Coleta
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                time.sleep(1)

            cards = page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"])
            urls = []
            for card in cards:
                link_elem = card.query_selector(self.dados_integracao["seletores"]["card_vaga_link"])
                if link_elem:
                    href = link_elem.get_attribute("href")
                    if href:
                        url = href if href.startswith("http") else f"https://portal.gupy.io{href}"
                        if url not in urls: urls.append(url)

            for url in urls:
                if limite != -1 and vagas_processadas >= limite: break
                if self.aplicar_vaga(page, url): vagas_processadas += 1
                time.sleep(2)
            context.close()
