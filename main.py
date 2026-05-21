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
        
        user_data_dir = self.config.get("chrome_user_data_windows")
        perfil = self.config.get("chrome_perfil_nome", "Default")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir, headless=False, channel="chrome",
                args=[f"--profile-directory={perfil}", "--start-maximized"]
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Instanciar automadores uma vez se possível
            from linkedin import LinkedInAutomator
            from gupy import GupyAutomator
            automator_li = LinkedInAutomator(self.config)
            automator_gp = GupyAutomator(self.config)
            
            vagas_restantes = list(lista_execucao)
            for vaga_url in lista_execucao:
                print(f"\n🚀 Prioritário: {vaga_url}")
                
                if "linkedin.com" in vaga_url:
                    automator_li._garantir_login(page)
                    automator_li.aplicar_vaga(page, vaga_url)
                elif "gupy.io" in vaga_url:
                    automator_gp.aplicar_vaga(page, vaga_url)
                else:
                    print(f"⚠️ Domínio não suportado: {vaga_url}")

                vagas_restantes.remove(vaga_url)
                self._salvar_json(self.lista_execucao_path, vagas_restantes)

            context.close()
        print("✅ Lista prioritária finalizada!")

    def rodar_ciclo_dominios(self):
        dominios_ativos = self._carregar_json(self.dominios_ativos_path)
        if not dominios_ativos: return

        for dominio in dominios_ativos:
            print(f"\n🌐 ================= ATIVANDO DOMÍNIO: {dominio} =================")
            try:
                if dominio == "linkedin.com":
                    from linkedin import LinkedInAutomator
                    LinkedInAutomator(self.config).executar_pesquisa("") # Termos são internos agora
                elif dominio == "gupy.io":
                    from gupy import GupyAutomator
                    GupyAutomator(self.config).executar_pesquisa("")
            except KeyboardInterrupt:
                self._pausar_ou_cancelar()
            except Exception as e:
                print(f"❌ Erro no domínio {dominio}: {e}")

    def _pausar_ou_cancelar(self):
        print("\n🛑 Interrupção detectada.")
        opcao = input("Digite 'C' para Cancelar ou 'P' para Pausar: ").strip().upper()
        if opcao == 'C': sys.exit(0)
        elif opcao == 'P': input("PAUSADO. ENTER para continuar...")

    def iniciar(self):
        loop_config = self.config.get("loops_sistema", 0)
        contador_loop = 0
        while True:
            print(f"\n--- 🔄 CICLO (Loop: {contador_loop}) ---")
            self.processar_lista_prioritaria()
            
            # Ajuste: Rodar para cada palavra-chave
            for termo in self.config["palavras_chave"]:
                print(f"\n🔍 [PESQUISA] Termo: {termo}")
                dominios_ativos = self._carregar_json(self.dominios_ativos_path)
                for dominio in dominios_ativos:
                    try:
                        if dominio == "linkedin.com":
                            from linkedin import LinkedInAutomator
                            LinkedInAutomator(self.config).executar_pesquisa(termo)
                        elif dominio == "gupy.io":
                            from gupy import GupyAutomator
                            GupyAutomator(self.config).executar_pesquisa(termo)
                    except KeyboardInterrupt: self._pausar_ou_cancelar()
                    except Exception as e: print(f"❌ Erro: {e}")

            print("\n📊 Atualizando estatísticas...")
            from estatisticas import AnalisadorEstatisticas
            try: AnalisadorEstatisticas().processar_metricas()
            except: pass

            contador_loop += 1
            if loop_config == 0 or (loop_config > 0 and contador_loop >= loop_config): break
            time.sleep(60)
       
if __name__ == "__main__":
    OrquestradorAutomacao().iniciar()
