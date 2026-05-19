É um sistema de enviar Currículos automático
---
Haverá um arquivo “.JSON” de integração onde haverá informações de QUAL e COMO fazer para cada site, passar de página, campos de formulário, onde anexar o CV etc.
Deve incluir (mas não limitado à): 
- Qual o site/domínio
- Passo à passo de execução (para o script saber o que fazer)
	- Onde pesquisa por novas páginas (campo e link + botão pesquisar)
		- Onde está o botão de próxima página
		- Onde estão as vagas
			- Título e descrição da vaga
			- Onde fica o botão de "enviar" vaga
		- Botão de "Candidatura Simples"
		- O que significa cada campo de descrição (ex.: Quantos anos de experiência em Python? (e salva o ID da tag, com a pergunta (de forma à identificá-la posteriormente))
				- E ESSE, depois de identificado, vai levar pra uma outra tabela de "Respostas.json" que terá um ID com as respostas (pra identificar entre as diferentes plataformas e perguntas a mesma resposta (Uma: "Anos de experiência em Python"; outra: "Quantos anos em Python?", ambas têm a mesma resposta))
---
GERAL:
- Haverá vários links e domínios de sites de vagas (ex.: Linkedin; Gupy etc)
- Fluxo de Exceção: Quando houver QUALQUER exceção, erro, ou coisa desconhecida que impeça de avançar, ele deverá SALVAR o link, declarar o passo onde parou, e salvar isso na "Lista à Ajustar", que irei atualizar manualmente o "Integracao.json" para implementar novas funcionalidades (ou criar mais um script específico pra tal site).
	- Eu irei ir conversando contigo para criar e atualizar os scripts de execução de cada site. 
- Ele deverá primeiro, checar a "Lista de Execução" onde estará salvo o link (vaga) do que foi ajustado manualmente. Depois de executado, ele deve eliminar o que foi executado. Se falhar deve seguir os passos anteriores de exceção
	- Depois de terminar toda a "Lista de Execução" seguirá vendo vaga por vaga da "Lista de Domínios ativos"
		- Nessa "Lista de Domínios ativos", é a que seleciono manualmente quais domínios ele deve buscar por vagas em ciclo, descrevo mais abaixo sobre a quantidade de vagas que pesquisará e enviará e como.
- Quando pesquisar as vagas por domínio, o sistema irá de vaga em vaga, de página em página, até:
	- Terminar a pesquisa
	- Terminar o limite configurado em "Configuracoes"
- Deverá ter um aviso de quando acabou a pesquisa de site e passar pro próximo termo da "Lista de Busca" (falo mais sobre em feedback)
- O Sistema DEVERÁ ter meios de CONFIRMAR a execução correta (se CADA campo foi preenchido corretamente antes de avançar, se FOI enviado mesmo, etc)
	- Caso falhe, use o fluxo de Exceção descrito anteriormente.
- Dúvidas PERGUNTE À MIM. 


---
O sistema DEVERÁ apresentar feedback ao usuário (por print ou de outra forma) de:
- Site/Domínio
- Qual página
- De CADA passo, cada Pergunta e resposta, cada clique 
- e também CADA CONFIRMAÇÃO (passou pra próxima página, enviado!, etc)
---
Configurações Manuais (Configurações):
- Quantas vagas ele pesquisará por domínio por palavra-chave? (-1 = até o fim; 0 = 0; 1 = 1 vaga etc). (ex.: 4, ele vai pesquisar "Python" e enviar para as 4 primeiras (dentro de todas as especificações descritas aqui (Se vai ou não candidatura simples, consultar "Integracao.json" etc)), depois vai pesquisar "Desenvolvedor FullStack" e as 4 primeiras, assim por diante)
- Quais palavras-chave ele deverá buscar na pesquisa de cada site. (ex.: ["Python"; "Desenvolvedor FullStack"; "Cientista de Dados"], ele pesquisará, Python, depois Desenvolvedor FullStack etc, dessa lista)
- SE ficará ou não em LOOP (depois de pesquisar X vagas de cada domínio da "Lista de Domínios Ativos" ele irá voltar do início OU não): (0=sem loop; -1 = infinito; 3= faz loop 3x de tudo do primeiro ao último domínio da lista).
- Manual Confirmation Step-by-step: Ele solicitará ao usuário para confirmar cada coisa (deverá ter um modo de EDITAR a resposta na pergunta, pode ser um msgbox com: Enviar e não salvar; Enviar e atualizar (vai sobrescrever a resposta antiga do arquivo "Respostas.json"); Campo de texto com a resposta sugerida configurada
	- DEVE suportar "Anexos", (aparece o nome do arquivo para anexo que será anexado e link para visualizar arquivo antes de enviar)
	- Link; Nome; Enviar e Atualizar; Enviar e não salvar; Selecionar outro;
	- SE possível, deve ter como visualizar esse anexo (.pdf, .docx, .txt) antes de enviar. (Será usado para CV, Covver letter etc)
		- SE não tiver o formato especificado para visualização, ele só deve avisar que não tem para o formato escolhido, e poder enviar mesmo assim (aí o link de abrir seria útil, se possível).
- Delay forçado de resposta para cada passo (segundos) (pode ser 0 (sem delay)): depois de ele executar o passo, antes de enviar ou passar para próxima página, esse tempo será para o usuário poder estar assistindo e poder CANCELAR ou PAUSAR.
---
Então temos as seguintes bases: 
- "Integracao.json"; 
- "Respostas.json"; 
- "ListaAAjustar" (não sei qual formato, decida);
- "ListaDeExecucao" (também não sei qual formato seria o melhor); 
- "ListaDeDomíniosAtivos"; 
- "Configurações" (talvez um .txt, ou .py mesmo, o que achar melhor); 
- "log.log" onde estará TUDO o que foi feito, DEVERÁ ter uma CÓPIA da: 
	- Com as seguintes informações (não limitado à):
		- Título da Vaga; 
		- link; 
		- domínio; 
		- Descrição da Vaga (se possível); 
		- DATA e HORA 
			- de Envio ("Submit"); 
			- Data e hora de começo de abertura do link (quando começou com aquela vaga);  
			- Data e Hora entre cada passo executado, ex.:
				- abrindo domínio, 
				- próxima página, 
				- respondendo forms de perguntas, 
				- anexando arquivo, 
				- enviado etc;
		- Quais erros ocorrem;
		-  Skips; 
		- Quais perguntas respondidas com quais respostas;
		- Sucesso/FALHA; etc
		- Outros Info. das vagas (então o sistema deve ter salvo pra buscar essas informações da cada vaga, ENTÃO QUANDO eu pedir para você criar um script para extrair as informações por webscrapping da vaga, DEVE (se possível) absorver também essas informações):
			- QUANDO a vaga foi POSTADA pela empresa
			- QUANTAS pessoas estavam concorrendo à vaga
			- QUAL empresa da vaga
			- LOCAL da vaga
			- REMOTO/HÍBRIDO/PRESENCIAL
			- Habilidades requiridas
			- 
	- com indentação e marcações para facilitar leitura,
	- E IMPORTANTE: DEVE ter uma CÓPIA num formato FÁCIL para .csv (para eu poder extrair estatísticas depois);
- "Configuracoes" (descrito anteriormente); 
- "Estatisticas.csv" aqui contém informações como: 
	- Quantos CVs já foram enviados (TOTAL)
	- Média da hora de envio
	- Média de envio vs data de postagem (quanto tempo desde a postagem da vaga até o envio)
	- Média de concorrência 
---
E Scripts: 
- Provavelmente terá um pra cada Site (eles deverão ser fáceis de chamar (talvez só colocar o nome do arquivo tipo: "linkedin.py") e puxar o main() (se for assim que funciona))
- Funcionalidades específicas (como clicar em botões (seguindo as instruções de "Integracao.json" para cada respectivo site); preencher campos (pelo descrito também em "Integracao.json") etc; . 
- Estatisticas.py: Ele processa "log.csv" faz o arquivo "Estatísticas.csv".
---
OUTROS:
- DEVE ter um comando para: CANCELAR, e outro pra PAUSAR o fluxo.
- FIQUE ATENTO, os sites quase 100% das vezes dão uma página de CONFIRMAÇÃO do envio, quando estiver fazendo o script webscrapping, puxe essa informação para CONFIRMAÇÃO, senão sinalize erro.
---
Caso você não saiba ou não entendeu algo, pare e pergunte, NUNCA INVENTE NADA.
---
