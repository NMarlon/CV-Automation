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
        self.dados_integracao = self._carregar_json("integracao.json")["linkedin.com"]
        self.respostas_db = self._carregar_json("respostas.json")
        
    def _carregar_json(self, caminho):
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def registrar_log(self, vaga_info, status, erro="", perguntas_respondidas=None):
        """Gera logs legíveis no log.log e tabulares no log_estatisticas.csv"""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Log textual legível
        with open("log.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{agora}] ---------- VAGA PROCESSADA ----------\n")
            f.write(f"Título: {vaga_info.get('titulo')}\nEmpresa: {vaga_info.get('empresa')}\n")
            f.write(f"Link: {vaga_info.get('link')}\nStatus: {status}\n")
            if erro: f.write(f"Erro encontrado: {erro}\n")
            if perguntas_respondidas: f.write(f"Perguntas respondidas: {json.dumps(perguntas_respondidas)}\n")
            f.write("-----------------------------------------\n")

        # 2. Log em CSV para processamento estatístico posterior
        csv_existe = os.path.exists("log_estatisticas.csv")
        with open("log_estatisticas.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not csv_existe:
                writer.writerow(["data_execucao", "titulo", "empresa", "link", "local", "modalidade", "postagem_bruta", "candidatos_bruto", "status", "erro"])
            writer.writerow([
                agora, vaga_info.get('titulo'), vaga_info.get('empresa'), vaga_info.get('link'),
                vaga_info.get('local'), vaga_info.get('modalidade'), vaga_info.get('postagem'),
                vaga_info.get('candidatos'), status, erro
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

    def executar_pesquisa(self, palavra_chave):
        """Inicia a sessão do Playwright acoplada ao Arc Browser para rodar a busca"""
        print(f"🔍 Iniciando busca por '{palavra_chave}' no LinkedIn...")
        
        # Caminho dinâmico adaptado para o Arc Browser no macOS
        user_data_dir = os.path.expanduser("~/Library/Application Support/Arc/User Data")
        
        with sync_playwright() as p:
            # Conecta à sua sessão ativa do Arc
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False, # Precisa ser visível para você assistir e usar Tkinter
                channel="chrome", # Força execução sobre a engine estável do Chrome/Arc
                args=["--no-sandbox"]
            )
            
            page = context.new_page()
            url_busca = self.dados_integracao["url_busca"].format(keyword=palavra_chave)
            page.goto(url_busca)
            page.wait_for_load_state("networkidle")
            
            vagas_processadas = 0
            limite_vagas = self.config.get("vagas_por_termo", -1)
            
            # Varredura das vagas da barra lateral esquerda
            lista_itens = page.query_selector_all(self.dados_integracao["seletores"]["lista_vagas"])
            urls_vagas_pagina = []
            
            for item in lista_itens:
                link_elem = item.query_selector(self.dados_integracao["seletores"]["card_vaga_link"])
                if link_elem:
                    href = link_elem.get_attribute("href")
                    # Limpa os parâmetros de tracking da URL
                    url_limpa = href.split("?")[0] if href else ""
                    if url_limpa and url_limpa not in urls_vagas_pagina:
                        urls_vagas_pagina.append(url_limpa)

            print(f"📦 Encontradas {len(urls_vagas_pagina)} vagas nesta página.")

            for url in urls_vagas_pagina:
                if limite_vagas != -1 and vagas_processadas >= limite_vagas:
                    print("🛑 Limite de vagas atingido para esta palavra-chave.")
                    break
                
                sucesso = self.aplicar_vaga(page, url)
                if sucesso:
                    vagas_processadas += 1
                
                time.sleep(2) # Pequeno respiro entre vagas

            context.close()
            print(f"🏁 Concluída pesquisa do termo '{palavra_chave}' no LinkedIn.")