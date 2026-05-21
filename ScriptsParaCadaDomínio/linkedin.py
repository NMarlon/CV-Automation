import os
import json
import time
import csv
import sys
import re
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
            f.write(f"\n[{agora}] ---------- VAGA LINKEDIN ----------\n")
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
            print(f"\n🛑 [PAUSA EM ERRO] Ocorreu um erro no passo: {passo}")
            print(f"🔗 Link: {link}")
            print(f"❌ Erro: {erro}")
            input("Pressione ENTER para continuar após resolver manualmente...")

    def validar_titulo(self, titulo):
        if not titulo: return False, "Título vazio"
        aprovados = self.config.get("titulos_aprovados", [])
        desaprovados = self.config.get("titulos_desaprovados", [])
        titulo_upper = titulo.upper()
        for d in desaprovados:
            if d.upper() in titulo_upper: return False, f"Palavra desaprovada: {d}"
        for a in aprovados:
            if a.upper() in titulo_upper: return True, ""
        return False, "Sem palavras-chave aprovadas"

    def responder_fluxo_formulario(self, page, vaga_info):
        seletores = self.dados_integracao["seletores"]
        perguntas_da_sessao = {}
        try:
            while True:
                time.sleep(self.config.get("delay_passo", 2))
                form_elements = page.query_selector_all(f"{seletores['modal_formulario']} .jobs-easy-apply-form-section__grouping")
                for element in form_elements:
                    label_elem = element.query_selector("label")
                    if not label_elem: continue
                    texto_pergunta = label_elem.inner_text().strip()
                    if not texto_pergunta or texto_pergunta in perguntas_da_sessao: continue

                    chave = self.respostas_db.get("perguntas_mapeadas", {}).get(texto_pergunta)
                    if chave:
                        resp = self.respostas_db.get("valores_respostas", {}).get(chave)
                        if self.config.get("confirmacao_manual"):
                            res_h = self.interface.confirmar_campo(texto_pergunta, resp, chave)
                            if res_h["acao"] == "cancelar": raise Exception("Cancelado pelo usuário")
                            resp, acao = res_h["resposta"], res_h["acao"]
                        else: resp, acao = resp, "auto"
                    else:
                        res_h = self.interface.perguntar_resposta_nova(texto_pergunta)
                        if res_h["acao"] == "cancelar": raise Exception("Cancelado pelo usuário")
                        resp, acao, chave = res_h["resposta"], res_h["acao"], res_h["chave"]

                    if acao == "salvar_atualizar":
                        self.respostas_db.setdefault("perguntas_mapeadas", {})[texto_pergunta] = chave
                        self.respostas_db.setdefault("valores_respostas", {})[chave] = resp
                        self._salvar_json("respostas.json", self.respostas_db)

                    input_elem = element.query_selector("input, select, textarea")
                    if input_elem:
                        tag = input_elem.evaluate("el => el.tagName")
                        if tag == "SELECT": input_elem.select_option(label=resp)
                        elif input_elem.get_attribute("type") == "radio":
                            for r in element.query_selector_all("input[type='radio']"):
                                r_l = page.query_selector(f"label[for='{r.get_attribute('id')}']")
                                if r_l and resp.lower() in r_l.inner_text().lower():
                                    r.click()
                                    break
                        else: input_elem.fill(resp)
                    perguntas_da_sessao[texto_pergunta] = resp

                btn_av = page.query_selector(seletores["botao_avancar_modal"])
                btn_rev = page.query_selector(seletores["botao_revisar_modal"])
                btn_env = page.query_selector(seletores["botao_enviar_vaga"])
                
                if btn_av and btn_av.is_visible(): btn_av.click()
                elif btn_rev and btn_rev.is_visible(): btn_rev.click()
                elif btn_env and btn_env.is_visible():
                    if "currículo" in page.content().lower() or "cv" in page.content().lower():
                        res_anexo = self.interface.validar_anexo(self.config.get("caminho_cv_padrao"))
                        if res_anexo["acao"] == "cancelar": raise Exception("Envio cancelado no CV")
                    btn_env.click()
                    time.sleep(3)
                    if page.query_selector(seletores["confirmacao_sucesso"]):
                        self.registrar_log(vaga_info, "SUCESSO")
                        page.keyboard.press("Escape")
                        return True
                    raise Exception("Sucesso não confirmado após envio")
                else: break
            return False
        except Exception as e:
            self.tratar_excecao(vaga_info["link"], "Formulário", e)
            self.registrar_log(vaga_info, "FALHA", str(e))
            return False

    def aplicar_vaga(self, page, url_vaga):
        seletores = self.dados_integracao["seletores"]
        vaga_info = {"link": url_vaga, "titulo": "N/A", "empresa": "N/A", "local": "N/A", "modalidade": "N/A", "postagem": "N/A", "candidatos": "N/A"}

        tentativas = self.config.get("tentativas_por_vaga", 4)
        intervalo = self.config.get("intervalo_tentativa", 20)

        for t in range(tentativas):
            try:
                print(f"🔗 Tentativa {t+1}/{tentativas}: Abrindo vaga {url_vaga}")
                page.goto(url_vaga, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3)

                # Extração Rica de Dados
                for chave in ["titulo_vaga", "empresa_vaga", "local_vaga", "modalidade_vaga", "data_postagem", "num_candidatos"]:
                    try:
                        el = page.locator(seletores.get(chave)).first
                        if el.is_visible(): vaga_info[chave.replace("_vaga", "").replace("num_", "").replace("data_", "")] = el.inner_text().strip()
                    except: pass

                val, mot = self.validar_titulo(vaga_info["titulo"])
                if not val:
                    print(f"⏭️ Pulando vaga por título: {vaga_info['titulo']} ({mot})")
                    self.registrar_log(vaga_info, "PULADA", titulo_pulado=vaga_info["titulo"])
                    return False

                btn = page.query_selector(seletores["botao_candidatura_simples"])
                if not btn:
                    print(f"⏭️ Vaga não possui botão de Candidatura Simplificada.")
                    self.registrar_log(vaga_info, "SKIP", "Não é Candidatura Simplificada")
                    return False

                print("🚀 Clicando em Candidatura Simplificada...")
                btn.click()
                page.wait_for_selector(seletores["modal_formulario"], timeout=15000)
                return self.responder_fluxo_formulario(page, vaga_info)
            except Exception as e:
                print(f"⚠️ Erro na tentativa {t+1} de aplicação: {e}")
                if t < tentativas - 1:
                    time.sleep(intervalo)
                else:
                    self.tratar_excecao(url_vaga, f"Tentativa Final Aplicação", e)
                    return False
        return False

    def _garantir_login(self, page):
        page.goto("https://www.linkedin.com/feed/", timeout=60000, wait_until="domcontentloaded")
        if "feed" in page.url: return
        page.goto("https://www.linkedin.com/login", timeout=60000, wait_until="domcontentloaded")
        email, senha = self.config.get("email"), self.config.get("senha")
        if email and senha:
            page.fill("input#username", email)
            page.fill("input#password", senha)
            page.click('button[type="submit"]')
            try: page.wait_for_url("**/feed/**", timeout=20000)
            except:
                print("⚠️ Login falhou ou requer Captcha.")
                page.pause()
        else: page.pause()

    def executar_pesquisa(self, palavra_chave):
        u_dir = self.config.get("chrome_user_data_windows")
        perfil = self.config.get("chrome_perfil_nome", "Default")
        tentativas_busca = self.config.get("tentativas_por_vaga", 4)
        intervalo = self.config.get("intervalo_tentativa", 20)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(u_dir, headless=False, channel="chrome", args=[f"--profile-directory={perfil}", "--start-maximized"])
            page = context.pages[0] if context.pages else context.new_page()
            
            try:
                self._garantir_login(page)
                v_enviadas, limite = 0, self.config.get("vagas_por_termo", 4)
                p_atual = 1

                while limite == -1 or v_enviadas < limite:
                    url_busca = self.dados_integracao["url_busca"].format(keyword=palavra_chave) + f"&start={(p_atual - 1) * 25}"

                    sucesso_busca = False
                    for b in range(tentativas_busca):
                        try:
                            print(f"🔍 Busca '{palavra_chave}' Pág {p_atual} (Tentativa {b+1})")
                            page.goto(url_busca, timeout=60000, wait_until="domcontentloaded")
                            time.sleep(5) # Aguarda renderização
                            sucesso_busca = True
                            break
                        except Exception as e:
                            print(f"⚠️ Erro ao carregar busca: {e}")
                            if b < tentativas_busca - 1: time.sleep(intervalo)

                    if not sucesso_busca:
                        self.tratar_excecao(url_busca, f"Carregar Pesquisa {palavra_chave} Pág {p_atual}", "Timeout excedido")
                        break

                    # Scroll lateral
                    seletor_lista = ".scaffold-layout__list"
                    if page.query_selector(seletor_lista):
                        for _ in range(4):
                            page.eval_on_selector(seletor_lista, "el => el.scrollTop += 800")
                            time.sleep(1)

                    cards = page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"])
                    if not cards:
                        print("🏁 Nenhuma vaga encontrada.")
                        break

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
                                urls_titulos.append((href.split("?")[0], t))

                    for u, t in urls_titulos:
                        if limite != -1 and v_enviadas >= limite: break
                        if self.aplicar_vaga(page, u):
                            v_enviadas += 1
                            print(f"✅ Candidatura enviada ({v_enviadas}/{limite})")
                        time.sleep(2)

                    if limite != -1 and v_enviadas >= limite: break

                    # Identificação de próxima página
                    estado_pag = page.query_selector(self.dados_integracao["seletores"]["paginacao_state"]) if "paginacao_state" in self.dados_integracao["seletores"] else None
                    if not estado_pag:
                        estado_pag = page.query_selector(".jobs-search-pagination__page-state")

                    if estado_pag:
                        texto_pag = estado_pag.inner_text() # "Página 1 de 40"
                        nums = re.findall(r'\d+', texto_pag)
                        if len(nums) >= 2:
                            atual, total = int(nums[0]), int(nums[1])
                            if atual >= total: break

                    btn_proxima = page.query_selector(self.dados_integracao["seletores"]["botao_proxima_pagina"])
                    if btn_proxima and btn_proxima.is_visible():
                        p_atual += 1
                    else:
                        break

            except Exception as e:
                print(f"❌ Erro crítico: {e}")
                if self.config.get("pausa_em_erro"):
                    input("PAUSA CRÍTICA. ENTER para continuar...")
            finally:
                context.close()
