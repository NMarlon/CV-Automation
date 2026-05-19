import os
import csv
import re
from datetime import datetime

class AnalisadorEstatisticas:
    def __init__(self):
        self.log_csv_path = "log_estatisticas.csv"
        self.output_csv_path = "Estatisticas.csv"

    def _converter_tempo_postagem_em_dias(self, texto_postagem):
        """Converte strings dinâmicas do LinkedIn (ex: 'há 3 dias', 'há 1 semana') em inteiros (dias)"""
        if not texto_postagem or not isinstance(texto_postagem, str):
            return None
            
        texto = texto_postagem.lower().strip()
        
        # Encontra o primeiro número na string
        numeros = re.findall(r'\d+', texto)
        quantidade = int(numeros[0]) if numeros else 1
        
        if "hora" in texto or "minuto" in texto or "segundo" in texto:
            return 0  # Postado hoje (menos de 1 dia)
        if "dia" in texto:
            return quantidade
        if "semana" in texto:
            return quantidade * 7
        if "mês" in texto or "mes" in texto:
            return quantidade * 30
            
        return None

    def _limpar_numero_candidatos(self, texto_candidatos):
        """Extrai apenas o número de candidatos de textos como '34 candidatos' ou 'Seja um dos primeiros...'"""
        if not texto_candidatos or not isinstance(texto_candidatos, str):
            return None
            
        texto = texto_candidatos.lower().strip()
        numeros = re.findall(r'\d+', texto)
        
        if numeros:
            return int(numeros[0])
        if "primeiros" in texto or "primeiras" in texto:
            return 5  # Estimativa baixa se for dos primeiros
            
        return None

    def processar_metricas(self):
        if not os.path.exists(self.log_csv_path):
            print(f"⚠️ Arquivo '{self.log_csv_path}' não encontrado. Execute o robô primeiro para gerar dados.")
            return

        total_enviados = 0
        soma_horas = 0
        contagem_horas = 0
        
        soma_tempo_postagem_dias = 0
        contagem_tempo_postagem = 0
        
        soma_concorrencia = 0
        contagem_concorrencia = 0

        # Lendo os logs tabulares crus
        with open(self.log_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Contabiliza apenas os envios concluídos com sucesso
                if row.get("status") == "SUCESSO":
                    total_enviados += 1
                    
                    # 1. Processamento da Hora de Envio
                    try:
                        data_exec = datetime.strptime(row["data_execucao"], "%Y-%m-%d %H:%M:%S")
                        soma_horas += data_exec.hour
                        contagem_horas += 1
                    except Exception:
                        pass
                        
                    # 2. Processamento do Tempo de Postagem vs Envio
                    dias_postagem = self._converter_tempo_postagem_em_dias(row.get("postagem_bruta"))
                    if dias_postagem is not None:
                        soma_tempo_postagem_dias += dias_postagem
                        contagem_tempo_postagem += 1
                        
                    # 3. Processamento da Média de Concorrência
                    candidatos = self._limpar_numero_candidatos(row.get("candidatos_bruto"))
                    if candidatos is not None:
                        soma_concorrencia += candidatos
                        contagem_concorrencia += 1

        # Cálculos Finais de Médias Eficientes
        media_hora_envio = round(soma_horas / contagem_horas, 1) if contagem_horas > 0 else 0
        media_tempo_postagem = round(soma_tempo_postagem_dias / contagem_tempo_postagem, 1) if contagem_tempo_postagem > 0 else 0
        media_concorrencia = round(soma_concorrencia / contagem_concorrencia, 1) if contagem_concorrencia > 0 else 0

        # Escrevendo o Relatório Consolidado de Estatísticas
        with open(self.output_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metrica", "Valor", "Descricao"])
            writer.writerow(["Total CVs Enviados", total_enviados, "Quantidade total de candidaturas bem-sucedidas"])
            writer.writerow(["Media Hora de Envio", f"{int(media_hora_envio)}h", "Média do horário do dia em que os envios ocorreram"])
            writer.writerow(["Media Tempo de Vaga (Dias)", f"{media_tempo_postagem} dias", "Média de dias entre a publicação da vaga e o seu envio"])
            writer.writerow(["Media de Concorrencia", f"{media_concorrencia} candidatos", "Média de pessoas concorrendo por vaga aplicada"])

        print(f"📊 Relatório '{self.output_csv_path}' atualizado com sucesso com base em {total_enviados} envios!")

if __name__ == "__main__":
    analisador = AnalisadorEstatisticas()
    analisador.processar_metricas()