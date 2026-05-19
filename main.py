import os
import json
import sys
import time
from configuracoes import CONFIG

# Adiciona o diretório de scripts ao PATH do Python para importação dinâmica
sys.path.append(os.path.abspath("ScriptsParaCadaDomínio"))

class OrquestradorAutomacao:
    def __init__(self):
        self.config = CONFIG
        self.lista_execucao_path = "ListaDeExecucao.json"
        self.dominios_ativos_path = "ListaDeDomíniosAtivos.json"
        



    def _carregar_json(self, caminho):
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _salvar_json(self, caminho, dados):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def processar_lista_prioritaria(self):
        """Consome e limpa a ListaDeExecucao.json primeiro"""
        lista_execucao = self._carregar_json(self.lista_execucao_path)
        if not lista_execucao:
            return

        print("\n⚡ [PRIORIDADE] Vagas encontradas na Lista de Execução Manual. Iniciando...")
        
        # Como as vagas possuem URLs completas, identificamos o domínio para chamar o script certo
        from linkedin import LinkedInAutomator
        # Instancia o robô temporariamente para limpar as pendências
        robo_linkedin = LinkedInAutomator(self.config)
        
        vagas_restantes = list(lista_execucao)
        for vaga_url in lista_execucao:
            print(f"\n🚀 Processando item prioritário: {vaga_url}")
            
            if "linkedin.com" in vaga_url:
                with robo_linkedin.conectar_sessao_ativa() as page:
                    sucesso = robo_linkedin.aplicar_vaga(page, vaga_url)
                
                # Se executou (com sucesso ou falhou jogando para ListaAAjustar), removemos da prioridade
                vagas_restantes.remove(vaga_url)
                self._salvar_json(self.lista_execucao_path, vagas_restantes)
            else:
                print(f"⚠️ Domínio contido em '{vaga_url}' ainda não possui script mapeado no main.py.")
        
        print("✅ Lista de Execução prioritária finalizada!")

    def rodar_ciclo_dominios(self):
        """Executa a busca cíclica baseada nos domínios ativos e palavras-chave"""
        dominios_ativos = self._carregar_json(self.dominios_ativos_path)
        if not dominios_ativos:
            print("⚠️ Nenhum domínio está ativo em 'ListaDeDomíniosAtivos.json'.")
            return

        for dominio in dominios_ativos:
            print(f"\n🌐 ================= ATIVANDO DOMÍNIO: {dominio} =================")
            
            if dominio == "linkedin.com":
                from ScriptsParaCadaDomínio.linkedin import LinkedInAutomator
                automator = LinkedInAutomator(self.config)
                
                for termo in self.config["palavras_chave"]:
                    print(f"\n🔄 [MUDANÇA DE TERMO] Iniciando pesquisa pela palavra-chave: '{termo}'")
                    
                    try:
                        automator.executar_pesquisa(termo)
                    except KeyboardInterrupt:
                        print("\n🛑 [PAUSA/CANCELAR] Interrupção manual detectada pelo teclado.")
                        opcao = input("Digite 'C' para Cancelar o sistema ou 'P' para Pausar (qualquer outra tecla para continuar): ").strip().upper()
                        if opcao == 'C':
                            print("Saindo do sistema de forma segura...")
                            sys.exit(0)
                        elif opcao == 'P':
                            print("Sistema em PAUSA. Pressione ENTER para retomar de onde parou...")
                            input()
                            
                    print(f"📢 Finalizada a busca por '{termo}' no domínio {dominio}. Próximo passo...")
            else:
                print(f"ℹ️ O domínio {dominio} está ativo, mas o script correspondente não foi acoplado ao main.py.")

    def iniciar(self):
        loop_config = self.config["loops_sistema"]
        contador_loop = 0
        
        while True:
            print(f"\n--- 🔄 INICIANDO CICLO GERAL DO SISTEMA (Loop Atual: {contador_loop}) ---")
            
            # Passo 1: Limpar as pendências que você ajustou manualmente
            self.processar_lista_prioritaria()
            
            # Passo 2: Rodar o fluxo padrão por palavras-chave
            self.rodar_ciclo_dominios()

            print("\n📊 Atualizando métricas e geração de relatórios...")
            from estatisticas import AnalisadorEstatisticas
            AnalisadorEstatisticas().processar_metricas()

            contador_loop += 1
            if loop_config == 0:
                print("\n🏁 Configuração sem loop (loops_sistema = 0). Automação finalizada com sucesso!")
                break
            elif loop_config > 0 and contador_loop >= loop_config:
                print(f"\n🏁 Limite de loops atingido ({loop_config}x). Automação finalizada com sucesso!")
                break
            
            print(f"\n💤 Aguardando 1 minuto antes de reiniciar o ciclo completo de loops...")
            time.sleep(60)
       
if __name__ == "__main__":
    orquestrador = OrquestradorAutomacao()
    orquestrador.iniciar()