import os
import csv
import re
from datetime import datetime

class AnalisadorEstatisticas:
    def __init__(self):
        self.log_csv_path = "log_estatisticas.csv"
        self.output_csv_path = "Estatisticas.csv"

    def _converter_tempo_postagem_em_dias(self, texto_postagem):
        if not texto_postagem or not isinstance(texto_postagem, str): return None
        texto = texto_postagem.lower().strip()
        numeros = re.findall(r'\d+', texto)
        quantidade = int(numeros[0]) if numeros else 1
        if any(x in texto for x in ["hora", "minuto", "segundo"]): return 0
        if "dia" in texto: return quantidade
        if "semana" in texto: return quantidade * 7
        if "mês" in texto or "mes" in texto: return quantidade * 30
        return None

    def _limpar_numero_candidatos(self, texto_candidatos):
        if not texto_candidatos or not isinstance(texto_candidatos, str): return None
        texto = texto_candidatos.lower().strip()
        numeros = re.findall(r'\d+', texto)
        if numeros: return int(numeros[0])
        if "primeiros" in texto or "primeiras" in texto: return 5
        return None

    def processar_metricas(self):
        if not os.path.exists(self.log_csv_path): return

        total_enviados = 0
        total_pulados = 0
        soma_horas = 0
        contagem_horas = 0
        soma_tempo_postagem_dias = 0
        contagem_tempo_postagem = 0
        soma_concorrencia = 0
        contagem_concorrencia = 0

        with open(self.log_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "SUCESSO":
                    total_enviados += 1
                    try:
                        data_exec = datetime.strptime(row["data_execucao"], "%Y-%m-%d %H:%M:%S")
                        soma_horas += data_exec.hour
                        contagem_horas += 1
                    except: pass

                    dias = self._converter_tempo_postagem_em_dias(row.get("postagem_bruta"))
                    if dias is not None:
                        soma_tempo_postagem_dias += dias
                        contagem_tempo_postagem += 1

                    cands = self._limpar_numero_candidatos(row.get("candidatos_bruto"))
                    if cands is not None:
                        soma_concorrencia += cands
                        contagem_concorrencia += 1
                elif row.get("status") == "PULADA":
                    total_pulados += 1

        media_h = round(soma_horas / contagem_horas, 1) if contagem_horas > 0 else 0
        media_p = round(soma_tempo_postagem_dias / contagem_tempo_postagem, 1) if contagem_tempo_postagem > 0 else 0
        media_c = round(soma_concorrencia / contagem_concorrencia, 1) if contagem_concorrencia > 0 else 0

        with open(self.output_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metrica", "Valor", "Descricao"])
            writer.writerow(["Total CVs Enviados", total_enviados, "Total de candidaturas bem-sucedidas"])
            writer.writerow(["Total Vagas Puladas", total_pulados, "Total de vagas ignoradas por filtros de título"])
            writer.writerow(["Media Hora de Envio", f"{int(media_h)}h", "Média do horário de envio"])
            writer.writerow(["Media Tempo de Vaga (Dias)", f"{media_p} dias", "Média de dias desde a postagem"])
            writer.writerow(["Media de Concorrencia", f"{media_c} candidatos", "Média de concorrentes"])
        print(f"📊 Relatório '{self.output_csv_path}' atualizado!")

if __name__ == "__main__":
    AnalisadorEstatisticas().processar_metricas()
