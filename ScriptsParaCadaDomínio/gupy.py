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
        if not os.path.exists("log_estatisticas.csv"):
            with open("log_estatisticas.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["data_execucao", "titulo", "empresa", "link", "local", "modalidade", "postagem_bruta", "candidatos_bruto", "status", "erro", "titulo_pulado"])

    def _carregar_json(self, caminho):
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except: return {}
        return {}

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def registrar_log(self, vaga_info, status, erro="", perguntas_respondidas=None, titulo_pulado=""):
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{agora}] ---------- VAGA GUPY ----------\n")
            f.write(f"Título: {vaga_info.get('titulo') or titulo_pulado}\nEmpresa: {vaga_info.get('empresa')}\nStatus: {status}\n")
            if erro: f.write(f"ERRO: {erro}\n")
            if titulo_pulado: f.write(f"MOTIVO: Título reprovado nos filtros.\n")
            f.write("-----------------------------------------\n")
        with open("log_estatisticas.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([agora, vaga_info.get('titulo'), vaga_info.get('empresa'), vaga_info.get('link'), vaga_info.get('local'), vaga_info.get('modalidade'), vaga_info.get('postagem'), vaga_info.get('candidatos'), status, erro, titulo_pulado])

    def tratar_excecao(self, link, passo, erro):
        print(f"⚠️ Falha no passo [{passo}]: {erro}")
        caminho_ajuste = "ListaAAjustar.json"
        lista_ajuste = self._carregar_json(caminho_ajuste)
        if not isinstance(lista_ajuste, list): lista_ajuste = []
        lista_ajuste.append({"url": link, "passo_falha": passo, "erro": str(erro), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        self._salvar_json(caminho_ajuste, lista_ajuste)

        if self.config.get("pausa_em_erro"):
            print(f"\n🛑 [PAUSA EM ERRO] {passo} | {erro}")
            input("Pressione ENTER para continuar...")

    def validar_titulo(self, titulo):
        if not titulo: return False, "Vazio"
        aprovados = self.config.get("titulos_aprovados", [])
        desaprovados = self.config.get("titulos_desaprovados", [])
        t_up = titulo.upper()
        for d in desaprovados:
            if d.upper() in t_up: return False, f"Reprovado: {d}"
        for a in aprovados:
            if a.upper() in t_up: return True, ""
        return False, "Sem palavras-chave aprovadas"

    def responder_fluxo_formulario(self, page, vaga_info):
        seletores = self.dados_integracao["seletores"]
        try:
            while True:
                time.sleep(self.config.get("delay_passo", 2))
                btn_p = page.query_selector(seletores["botao_avancar_modal"])
                btn_e = page.query_selector(seletores["botao_enviar_vaga"])
                if btn_e and btn_e.is_visible():
                    btn_e.click()
                    time.sleep(3)
                    if page.query_selector(seletores["confirmacao_sucesso"]):
                        self.registrar_log(vaga_info, "SUCESSO")
                        return True
                    break
                elif btn_p and btn_p.is_visible(): btn_p.click()
                else: break
            return False
        except Exception as e:
            self.tratar_excecao(vaga_info["link"], "Gupy Form", e)
            self.registrar_log(vaga_info, "FALHA", str(e))
            return False

    def aplicar_vaga(self, page, url_vaga):
        seletores = self.dados_integracao["seletores"]
        vaga_info = {"link": url_vaga, "titulo": "Gupy Job", "empresa": "N/A"}

        tentativas = self.config.get("tentativas_por_vaga", 4)
        intervalo = self.config.get("intervalo_tentativa", 20)

        for t in range(tentativas):
            try:
                page.goto(url_vaga, timeout=60000)
                page.wait_for_load_state("networkidle")
                v_t = page.locator(seletores["titulo_vaga"]).first
                if v_t.is_visible(): vaga_info["titulo"] = v_t.inner_text().strip()

                val, mot = self.validar_titulo(vaga_info["titulo"])
                if not val:
                    self.registrar_log(vaga_info, "PULADA", titulo_pulado=vaga_info["titulo"])
                    return False

                btn = page.query_selector(seletores["botao_candidatura_simples"])
                if btn:
                    btn.click()
                    time.sleep(2)
                    return self.responder_fluxo_formulario(page, vaga_info)
                return False
            except Exception as e:
                print(f"⚠️ Erro Gupy (Tentativa {t+1}): {e}")
                if t < tentativas - 1: time.sleep(intervalo)
                else:
                    self.tratar_excecao(url_vaga, "Gupy App Final", e)
                    return False
        return False

    def executar_pesquisa(self, palavra_chave):
        u_dir = self.config.get("chrome_user_data_windows")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(u_dir, headless=False, channel="chrome", args=["--start-maximized"])
            page = context.pages[0] if context.pages else context.new_page()

            try:
                v_enviadas, limite = 0, self.config.get("vagas_por_termo", 4)
                offset = 0
                while limite == -1 or v_enviadas < limite:
                    url = self.dados_integracao["url_busca"].format(keyword=palavra_chave) + f"&offset={offset}"
                    page.goto(url, timeout=60000)
                    page.wait_for_load_state("networkidle")

                    cards = page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"])
                    if not cards: break

                    urls_titulos = []
                    for card in cards:
                        l_el = card.query_selector(self.dados_integracao["seletores"]["card_vaga_link"])
                        if l_el:
                            t = l_el.inner_text().strip()
                            v, _ = self.validar_titulo(t)
                            if not v:
                                self.registrar_log({"link": "N/A", "empresa": "N/A"}, "PULADA", titulo_pulado=t)
                                continue
                            href = l_el.get_attribute("href")
                            if href:
                                u_full = href if href.startswith("http") else f"https://portal.gupy.io{href}"
                                urls_titulos.append((u_full, t))

                    for u, t in urls_titulos:
                        if limite != -1 and v_enviadas >= limite: break
                        if self.aplicar_vaga(page, u): v_enviadas += 1
                        time.sleep(2)

                    if limite != -1 and v_enviadas >= limite: break
                    offset += 10
                    if len(cards) < 10: break
            finally:
                context.close()
