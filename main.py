import os
import json
import sys
import time
from configuracoes import CONFIG
from playwright.sync_api import sync_playwright

# Adiciona o diretório de scripts ao PATH do Python
sys.path.append(os.path.abspath("ScriptsParaCadaDomínio"))

class OrquestradorAutomacao:
    def __init__(self):
        self.config = CONFIG
        self.lista_execucao_path = "ListaDeExecucao.json"
        self.dominios_ativos_path = "ListaDeDomíniosAtivos.json"
        self.lista_ajustar_path = "ListaAAjustar.json"

    def _carregar_json(self, caminho):
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except: return []
        return []

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def processar_lista_prioritaria(self):
        lista_execucao = self._carregar_json(self.lista_execucao_path)
        if not lista_execucao: return

        print("\n⚡ [PRIORIDADE] Processando Lista de Execução Manual...")
        u_dir = self.config.get("chrome_user_data_windows")
        perfil = self.config.get("chrome_perfil_nome", "Default")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                u_dir, headless=False, channel="chrome",
                args=[f"--profile-directory={perfil}", "--start-maximized"]
            )
            page = context.pages[0] if context.pages else context.new_page()

            from linkedin import LinkedInAutomator
            from gupy import GupyAutomator
            automator_li = LinkedInAutomator(self.config)
            automator_gp = GupyAutomator(self.config)

            v_restantes = list(lista_execucao)
            for url in lista_execucao:
                print(f"\n🚀 Prioritário: {url}")
                if "linkedin.com" in url:
                    automator_li._garantir_login(page)
                    automator_li.aplicar_vaga(page, url)
                elif "gupy.io" in url:
                    automator_gp.aplicar_vaga(page, url)
                else:
                    print(f"⚠️ Domínio não suportado: {url}")

                v_restantes.remove(url)
                self._salvar_json(self.lista_execucao_path, v_restantes)
            context.close()
        print("✅ Lista prioritária finalizada!")

    def rodar_ciclo(self):
        dominios = self._carregar_json(self.dominios_ativos_path)
        if not dominios: return

        for dom in dominios:
            print(f"\n🌐 ================= DOMÍNIO: {dom} =================")
            for termo in self.config["palavras_chave"]:
                print(f"\n🔍 [PESQUISA] Termo: {termo} em {dom}")
                try:
                    if dom == "linkedin.com":
                        from linkedin import LinkedInAutomator
                        LinkedInAutomator(self.config).executar_pesquisa(termo)
                    elif dom == "gupy.io":
                        from gupy import GupyAutomator
                        GupyAutomator(self.config).executar_pesquisa(termo)
                except KeyboardInterrupt:
                    self._pausar_ou_cancelar()
                except Exception as e:
                    print(f"❌ Erro crítico em {dom} / {termo}: {e}")

    def _pausar_ou_cancelar(self):
        op = input("\n🛑 PAUSA (P) ou CANCELAR (C)? ").strip().upper()
        if op == 'C': sys.exit(0)
        elif op == 'P': input("PAUSADO. ENTER para retomar...")

    def iniciar(self):
        loop_cfg = self.config.get("loops_sistema", 0)
        c_loop = 0
        while True:
            print(f"\n--- 🔄 CICLO GERAL (Loop: {c_loop}) ---")
            self.processar_lista_prioritaria()
            self.rodar_ciclo()

            print("\n📊 Atualizando estatísticas...")
            from estatisticas import AnalisadorEstatisticas
            try: AnalisadorEstatisticas().processar_metricas()
            except: pass

            c_loop += 1
            if loop_cfg == 0 or (loop_cfg > 0 and c_loop >= loop_cfg): break
            print(f"\n💤 Aguardando 1 minuto...")
            time.sleep(60)
       
if __name__ == "__main__":
    OrquestradorAutomacao().iniciar()
