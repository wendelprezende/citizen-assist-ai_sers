import csv
import json
import time
from datetime import datetime

from energia import (CalculadoraEnergia, Equipamento, Residencia,
                     formatar_moeda, formatar_numero)

CAMPOS_CSV = ["data", "origem", "pergunta", "orientacao_id", "encontrou",
              "ajudou", "tentativas", "tempo_segundos", "facilidade"]


def contem_dado_pessoal(texto):
    digitos = 0
    for caractere in texto:
        if caractere.isdigit():
            digitos += 1
    return digitos >= 8 or "@" in texto


class Assistente:
    def __init__(self, nome, base, caminho_historico="data/historico.json", dados_energia=None):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.dados_energia = dados_energia
        self.historico = self.carregar_historico()
        self.inicio_sessao = len(self.historico)

    def carregar_historico(self):
        try:
            with open(self.caminho_historico, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            print("Histórico ilegível. Começando um novo.")
            return []

        if not isinstance(dados, list):
            print("Histórico ilegível. Começando um novo.")
            return []
        return dados

    def salvar_historico(self):
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=4)
        except OSError:
            print("Não foi possível salvar o histórico.")

    def ler_sim_nao(self, texto):
        while True:
            resposta = input(texto).strip().lower()
            if resposta in ("s", "n"):
                return resposta == "s"
            print("Digite apenas s ou n.")

    def registrar(self, origem, pergunta, orientacao_id, encontrou, ajudou, tentativas, inicio):
        atendimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origem": origem,
            "pergunta": pergunta,
            "orientacao_id": orientacao_id,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_segundos": round(time.time() - inicio, 1),
        }
        self.historico.append(atendimento)
        self.salvar_historico()

    def perguntar(self):
        inicio = time.time()
        tentativas = 0
        encontrou = False
        orientacao_id = None
        ultima_pergunta = ""

        while True:
            pergunta = input("Digite sua dúvida (0 para voltar): ").strip()

            if pergunta == "0":
                if tentativas > 0:
                    self.registrar("pergunta", ultima_pergunta, orientacao_id,
                                   encontrou, False, tentativas, inicio)
                return

            if pergunta == "":
                print("Você não digitou nada. Escreva sua dúvida.")
                continue

            if contem_dado_pessoal(pergunta):
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva.")
                continue

            tentativas += 1
            ultima_pergunta = pergunta
            resultados = self.base.buscar(pergunta)

            if not resultados or resultados[0][0] < 3:
                print("Não encontrei uma orientação para essa dúvida.")
                print("Tente outras palavras (por exemplo, o nome do documento) "
                      "ou volte e use as categorias.")
                continue

            encontrou = True
            pontos, melhor = resultados[0]
            orientacao_id = melhor.id
            nivel = "ALTA" if pontos >= 6 else "MÉDIA"

            print(f"\nConfiança da resposta: {nivel} ({pontos} pontos)")
            melhor.exibir()

            alternativas = [o for p, o in resultados[1:3] if p >= 3]
            if alternativas:
                print("Veja também:")
                for alternativa in alternativas:
                    print(f" - {alternativa.titulo}")

            if self.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): "):
                self.registrar("pergunta", ultima_pergunta, orientacao_id,
                               True, True, tentativas, inicio)
                return

    def ler_opcao(self, total):
        while True:
            entrada = input("Escolha uma opção: ").strip()
            if entrada.isdecimal() and int(entrada) <= total:
                return int(entrada)
            print(f"Opção inválida. Digite um número de 0 a {total}.")

    def navegar(self):
        categorias = self.base.categorias()
        if not categorias:
            print("Nenhuma categoria disponível.")
            return

        while True:
            inicio = time.time()
            print("\nCategorias:")
            for numero, categoria in enumerate(categorias, start=1):
                print(f" {numero} - {categoria}")
            print(" 0 - Voltar")

            opcao = self.ler_opcao(len(categorias))
            if opcao == 0:
                return
            self.navegar_categoria(categorias[opcao - 1], inicio)

    def navegar_categoria(self, categoria, inicio):
        orientacoes = self.base.por_categoria(categoria)

        while True:
            print(f"\n{categoria}:")
            for numero, orientacao in enumerate(orientacoes, start=1):
                print(f" {numero} - {orientacao.titulo}")
            print(" 0 - Voltar")

            opcao = self.ler_opcao(len(orientacoes))
            if opcao == 0:
                return

            orientacao = orientacoes[opcao - 1]
            print()
            orientacao.exibir()
            ajudou = self.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("categoria", orientacao.titulo, orientacao.id,
                           True, ajudou, 1, inicio)
            inicio = time.time()

    def pedir_nota_facilidade(self):
        sessao = self.historico[self.inicio_sessao:]
        if not sessao:
            return

        while True:
            entrada = input("De 1 a 5, o quão fácil foi usar o assistente? ").strip()
            if entrada in ("1", "2", "3", "4", "5"):
                nota = int(entrada)
                break
            print("Digite um número de 1 a 5.")

        for atendimento in sessao:
            atendimento["facilidade"] = nota
        self.salvar_historico()

    def indicadores(self):
        total = len(self.historico)
        if total == 0:
            print("Ainda não há atendimentos registrados.")
            return

        encontrados = 0
        ajudaram = 0
        soma_tempo = 0
        soma_tentativas = 0
        notas = []
        sem_solucao = []

        for atendimento in self.historico:
            if atendimento["encontrou"]:
                encontrados += 1
            if atendimento["ajudou"]:
                ajudaram += 1
                soma_tempo += atendimento["tempo_segundos"]
            else:
                if atendimento["pergunta"] not in sem_solucao:
                    sem_solucao.append(atendimento["pergunta"])
            soma_tentativas += atendimento["tentativas"]
            if "facilidade" in atendimento:
                notas.append(atendimento["facilidade"])

        print("\n=== Indicadores ===")
        print(f"Atendimentos registrados: {total}")
        print(f"Resposta encontrada: {encontrados / total * 100:.1f}%")
        print(f"Taxa de acerto (ajudou): {ajudaram / total * 100:.1f}%")
        if ajudaram > 0:
            print(f"Tempo médio para encontrar: {soma_tempo / ajudaram:.1f} s")
        else:
            print("Tempo médio para encontrar: sem dados")
        print(f"Tentativas por atendimento: {soma_tentativas / total:.1f}")
        if notas:
            print(f"Facilidade de uso (1 a 5): {sum(notas) / len(notas):.1f}")
        else:
            print("Facilidade de uso (1 a 5): sem dados")
        print("Dúvidas sem solução:")
        if sem_solucao:
            for duvida in sem_solucao:
                print(f" - {duvida}")
        else:
            print(" (nenhuma)")

    def exportar_csv(self, caminho="data/atendimentos.csv"):
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV, restval="")
                escritor.writeheader()
                escritor.writerows(self.historico)
        except OSError:
            print("Não foi possível exportar o CSV.")
            return
        print(f"{len(self.historico)} atendimentos exportados para {caminho}.")

    def ler_numero(self, texto, minimo, maximo, padrao=None):
        while True:
            entrada = input(texto).strip().replace(",", ".")
            if entrada == "" and padrao is not None:
                return padrao
            try:
                valor = float(entrada)
            except ValueError:
                print("Digite um número (exemplo: 2 ou 1,5).")
                continue
            if minimo <= valor <= maximo:
                return valor
            print(f"Digite um valor entre {minimo} e {maximo}.")

    def ler_inteiro(self, texto, minimo, maximo, padrao=None):
        while True:
            valor = self.ler_numero(texto, minimo, maximo, padrao)
            if valor == int(valor):
                return int(valor)
            print("Digite um número inteiro.")

    def perguntar_equipamento(self, item):
        fator_uso = item.get("fator_uso", 1.0)
        if item["kwh_mes_fixo"] is not None:
            return Equipamento(item["id"], item["nome"], item["potencia_w"], 0,
                               item["dias_mes"], item["kwh_mes_fixo"], fator_uso)
        horas = self.ler_numero(f"Horas de uso por dia de '{item['nome']}' [{item['horas_dia']}]: ",
                                0.1, 24, item["horas_dia"])
        dias = self.ler_inteiro(f"Dias de uso por mês [{item['dias_mes']}]: ",
                                1, 31, item["dias_mes"])
        return Equipamento(item["id"], item["nome"], item["potencia_w"], horas, dias,
                           None, fator_uso)

    def montar_residencia(self):
        print("\nVocê mora:")
        print(" 1 - Sozinho(a)")
        print(" 2 - Com a família")
        print(" 0 - Voltar")
        opcao = self.ler_opcao(2)
        if opcao == 0:
            return None

        if opcao == 1:
            residencia = Residencia("sozinho", 1)
        else:
            moradores = self.ler_inteiro("Quantas pessoas moram na casa? [4]: ", 2, 10, 4)
            residencia = Residencia("familia", moradores)

        catalogo = self.dados_energia.catalogo()
        chuveiro = [item for item in catalogo if item["id"] == "chuveiro"][0]
        minutos = self.ler_numero(
            f"Minutos de banho por pessoa [{self.dados_energia.hipotese('minutos_banho_por_pessoa')}]: ",
            1, 60, self.dados_energia.hipotese("minutos_banho_por_pessoa"))
        potencia = self.ler_numero(
            f"Potência do chuveiro em watts (veja a etiqueta) [{chuveiro['potencia_w']}]: ",
            500, 10000, chuveiro["potencia_w"])
        horas_chuveiro = minutos * residencia.moradores / 60
        residencia.adicionar(Equipamento("chuveiro", chuveiro["nome"], potencia,
                                         horas_chuveiro, chuveiro["dias_mes"]))

        aparelhos = [item for item in catalogo if item["id"] != "chuveiro"]
        escolhidos = []
        while True:
            print("\nAdicione os aparelhos da casa (0 para terminar):")
            for numero, item in enumerate(aparelhos, start=1):
                marca = " (já adicionado)" if item["id"] in escolhidos else ""
                print(f" {numero} - {item['nome']}{marca}")
            print(" 0 - Terminar a lista")
            opcao = self.ler_opcao(len(aparelhos))
            if opcao == 0:
                break
            item = aparelhos[opcao - 1]
            ja_tem_geladeira = any(i.startswith("geladeira") for i in escolhidos)
            if item["id"] in escolhidos:
                print("Esse aparelho já foi adicionado.")
            elif item["id"].startswith("geladeira") and ja_tem_geladeira:
                print("Você já adicionou uma geladeira.")
            else:
                residencia.adicionar(self.perguntar_equipamento(item))
                escolhidos.append(item["id"])
        return residencia

    def escolher_bandeira(self):
        info = self.dados_energia.dados["bandeiras"]
        nomes = self.dados_energia.bandeiras()
        print("\nBandeira tarifária:")
        for numero, nome in enumerate(nomes, start=1):
            valor = info["valores"][nome]
            marca = f" (vigente em {info['referencia']})" if nome == info["vigente"] else ""
            print(f" {numero} - {nome.replace('_', ' ')}: {formatar_moeda(valor)} por 100 kWh{marca}")
        print(" 0 - Voltar")
        opcao = self.ler_opcao(len(nomes))
        if opcao == 0:
            return None
        return nomes[opcao - 1]

    def mostrar_resultados_energia(self, residencia, calculadora, resultados, bandeira):
        base = resultados["base"]
        eficiencia = resultados["eficiencia"]
        minimo = resultados["assinatura_min"]
        maximo = resultados["assinatura_max"]
        dados = self.dados_energia.dados

        print("\n=== Resultado (ESTIMATIVA) ===")
        print(f"Tarifa: {formatar_numero(calculadora.tarifa.valor_kwh(), 5)} R$/kWh "
              f"({dados['tarifa']['distribuidora']}, {dados['tarifa']['classe']}, "
              f"bandeira {bandeira.replace('_', ' ')}), sem impostos.")
        print(f"Consumo estimado: {formatar_numero(base['kwh_mes'], 1)} kWh por mês "
              f"({residencia.moradores} pessoa(s)).")
        print("Maiores consumidores:")
        for posicao, (kwh, nome) in enumerate(residencia.consumo_por_equipamento()[:3], start=1):
            print(f" {posicao}. {nome}: {formatar_numero(kwh, 1)} kWh por mês")

        print("\nComparação em 12 meses (mesma casa, mesma tarifa):")
        print(f"1) {base['nome']}")
        print(f"   Custo: {formatar_moeda(base['custo_mes'])} por mês | {formatar_moeda(base['custo_ano'])} por ano")
        print(f"2) {eficiencia['nome']}")
        print(f"   {eficiencia['descricao']}")
        porcentagem = eficiencia["economia_ano"] / base["custo_ano"] * 100 if base["custo_ano"] else 0
        print(f"   Custo: {formatar_moeda(eficiencia['custo_mes'])} por mês | {formatar_moeda(eficiencia['custo_ano'])} por ano")
        print(f"   Economia: {formatar_moeda(eficiencia['economia_ano'])} por ano ({formatar_numero(porcentagem, 1)}%)"
              f" | CO2 evitado: {formatar_numero(eficiencia['emissao_evitada_kg_ano'], 1)} kg por ano")
        print("3) Energia solar por assinatura (fonte renovável)")
        print(f"   {maximo['descricao']}")
        print(f"   Economia: {formatar_moeda(minimo['economia_ano'])} a {formatar_moeda(maximo['economia_ano'])} por ano "
              f"(desconto de {minimo['desconto'] * 100:.0f}% a {maximo['desconto'] * 100:.0f}%)")
        print("   Sem investimento inicial. Impacto em CO2 não calculado (a matriz elétrica já é muito limpa).")

        assinatura = dados["assinatura_solar"]
        conta_minima = assinatura["conta_minima_citada_reais"]
        print("\nPontos de atenção:")
        if base["custo_mes"] < conta_minima[0]:
            print(f" - Sua conta estimada ({formatar_moeda(base['custo_mes'])} por mês, sem impostos) fica abaixo "
                  f"de R$ {conta_minima[0]} a R$ {conta_minima[1]}, mínimo citado por várias empresas de assinatura.")
        print(f" - {assinatura['risco_regulatorio']}")
        print(" - A economia da eficiência depende de você mudar os hábitos.")
        print(" - Impostos (como o ICMS) e a taxa de iluminação pública não estão incluídos.")

        print("\nPremissas e fontes:")
        print(f" - Tarifa [{dados['tarifa']['tipo']}]: {dados['tarifa']['norma']}. Fonte: {dados['tarifa']['fonte']}")
        print(f" - Bandeiras [{dados['bandeiras']['tipo']}]: {dados['bandeiras']['fonte']}")
        print(f" - Aparelhos [estimado]: valores médios de tabela (a potência real está na etiqueta). Fonte: {dados['equipamentos_origem']['fonte']}")
        print(f" - Eficiência: banho {self.dados_energia.hipotese('reducao_tempo_banho') * 100:.0f}% mais curto (hipótese do cenário), "
              f"stand-by até {self.dados_energia.hipotese('reducao_standby') * 100:.0f}% (Cemig) e "
              f"{self.dados_energia.hipotese('parcela_ar_trocada_por_ventilador') * 100:.0f}% das horas do ar-condicionado no ventilador (hipótese).")
        print(f" - Assinatura [estimado]: desconto de {assinatura['desconto_minimo'] * 100:.0f}% a {assinatura['desconto_maximo'] * 100:.0f}%, faixa divulgada pela imprensa (varia por contrato).")
        print(f" - Fator de emissão [oficial, média do grupo]: {formatar_numero(self.dados_energia.fator_emissao(), 4)} kg CO2/kWh (MCTI).")
        print("AVISO: estimativa para orientação, sem garantia de economia. Este assistente NÃO é um canal oficial.")

    def calcular_energia(self):
        if self.dados_energia is None:
            print("O módulo de energia não está disponível (verifique data/energia_dados.json).")
            return

        inicio = time.time()
        print("\n=== Calcular consumo e economia de energia ===")
        print("Os resultados são ESTIMATIVAS. Não digite dados pessoais.")
        print("Pressione Enter para usar o valor sugerido entre colchetes.")

        residencia = self.montar_residencia()
        if residencia is None:
            return
        bandeira = self.escolher_bandeira()
        if bandeira is None:
            return

        calculadora = CalculadoraEnergia(self.dados_energia, bandeira)
        resultados = calculadora.comparar(residencia)
        self.mostrar_resultados_energia(residencia, calculadora, resultados, bandeira)

        ajudou = self.ler_sim_nao("Esse cálculo foi útil? (s/n): ")
        self.registrar("energia", f"calculo de energia ({residencia.tipo})", None,
                       True, ajudou, 1, inicio)
