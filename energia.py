import json

MESES_ANO = 12  # período de referência comum: 12 meses


class DadosEnergia:
    def __init__(self, caminho):
        self.caminho = caminho
        self.dados = {}

    def carregar(self):
        self.dados = {}
        try:
            with open(self.caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            print("Dados de energia não encontrados.")
            return False
        except json.JSONDecodeError:
            print("Dados de energia corrompidos.")
            return False

        if not isinstance(dados, dict):
            print("Dados de energia corrompidos.")
            return False

        for chave in ("tarifa", "bandeiras", "emissao", "equipamentos",
                      "hipoteses", "assinatura_solar"):
            if chave not in dados:
                print(f"Dados de energia incompletos (falta '{chave}').")
                return False

        self.dados = dados
        return True

    def tarifa(self, bandeira="verde"):
        base = self.dados["tarifa"]["kwh_sem_tributos"]
        adicional_100kwh = self.dados["bandeiras"]["valores"][bandeira]
        return Tarifa(base, adicional_100kwh)

    def bandeiras(self):
        return list(self.dados["bandeiras"]["valores"].keys())

    def fator_emissao(self):
        return self.dados["emissao"]["fator_kg_co2_por_kwh"]

    def catalogo(self):
        return self.dados["equipamentos"]

    def hipotese(self, nome):
        return self.dados["hipoteses"][nome]["valor"]

    def assinatura(self):
        return self.dados["assinatura_solar"]


class Tarifa:
    def __init__(self, kwh_sem_tributos, adicional_bandeira_100kwh=0.0):
        self.kwh_sem_tributos = kwh_sem_tributos
        self.adicional_bandeira_100kwh = adicional_bandeira_100kwh

    def valor_kwh(self):
        return self.kwh_sem_tributos + self.adicional_bandeira_100kwh / 100

    def custo(self, kwh):
        return kwh * self.valor_kwh()


class Equipamento:
    def __init__(self, id, nome, potencia_w, horas_dia, dias_mes,
                 kwh_mes_fixo=None, fator_uso=1.0):
        self.id = id
        self.nome = nome
        self.potencia_w = potencia_w
        self.horas_dia = horas_dia
        self.dias_mes = dias_mes
        self.kwh_mes_fixo = kwh_mes_fixo
        self.fator_uso = fator_uso

    def consumo_mensal_kwh(self):
        if self.kwh_mes_fixo is not None:
            return self.kwh_mes_fixo
        return self.potencia_w * self.horas_dia * self.dias_mes / 1000 * self.fator_uso


class Residencia:
    def __init__(self, tipo, moradores):
        self.tipo = tipo
        self.moradores = moradores
        self.equipamentos = []

    def adicionar(self, equipamento):
        self.equipamentos.append(equipamento)

    def consumo_mensal_kwh(self):
        total = 0
        for equipamento in self.equipamentos:
            total += equipamento.consumo_mensal_kwh()
        return total

    def consumo_por_equipamento(self):
        lista = []
        for equipamento in self.equipamentos:
            lista.append((equipamento.consumo_mensal_kwh(), equipamento.nome))
        lista.sort(key=lambda item: item[0], reverse=True)
        return lista


class CalculadoraEnergia:
    def __init__(self, dados, bandeira="verde"):
        self.dados = dados
        self.tarifa = dados.tarifa(bandeira)
        self.fator = dados.fator_emissao()

    def _resultado(self, nome, kwh_mes, base_kwh_mes, descricao):
        custo_mes = self.tarifa.custo(kwh_mes)
        custo_base_mes = self.tarifa.custo(base_kwh_mes)
        economia_kwh_ano = (base_kwh_mes - kwh_mes) * MESES_ANO
        return {
            "nome": nome,
            "descricao": descricao,
            "kwh_mes": kwh_mes,
            "custo_mes": custo_mes,
            "custo_ano": custo_mes * MESES_ANO,
            "economia_mes": custo_base_mes - custo_mes,
            "economia_ano": (custo_base_mes - custo_mes) * MESES_ANO,
            "emissao_evitada_kg_ano": economia_kwh_ano * self.fator,
        }

    def cenario_base(self, residencia):
        kwh = residencia.consumo_mensal_kwh()
        return self._resultado("Uso atual (referência)", kwh, kwh,
                               "Hábitos e equipamentos informados, sem mudanças.")

    def consumo_eficiente_kwh(self, residencia):
        reducao_banho = self.dados.hipotese("reducao_tempo_banho")
        reducao_standby = self.dados.hipotese("reducao_standby")
        parcela_ar = self.dados.hipotese("parcela_ar_trocada_por_ventilador")
        aparelhos_standby = self.dados.dados["hipoteses"]["aparelhos_standby"]
        potencia_ventilador = 0
        for item in self.dados.catalogo():
            if item["id"] == "ventilador":
                potencia_ventilador = item["potencia_w"]

        total = 0
        for equipamento in residencia.equipamentos:
            kwh = equipamento.consumo_mensal_kwh()
            if equipamento.id == "chuveiro":
                kwh = kwh * (1 - reducao_banho)
            elif equipamento.id in aparelhos_standby:
                kwh = kwh * (1 - reducao_standby)
            elif equipamento.id == "ar_condicionado":
                kwh_ventilador = (potencia_ventilador * equipamento.horas_dia
                                  * equipamento.dias_mes / 1000)  # ventilador liga o tempo todo
                kwh = kwh * (1 - parcela_ar) + kwh_ventilador * parcela_ar
            total += kwh
        return total

    def cenario_eficiencia(self, residencia):
        base = residencia.consumo_mensal_kwh()
        eficiente = self.consumo_eficiente_kwh(residencia)
        return self._resultado(
            "Eficiência energética (hábitos e uso)", eficiente, base,
            "Banho mais curto, stand-by desligado e ventilador no lugar do ar-condicionado.")

    def cenario_assinatura(self, residencia, desconto):
        base = residencia.consumo_mensal_kwh()
        custo_base = self.tarifa.custo(base)
        custo_mes = custo_base * (1 - desconto)
        economia_mes = custo_base - custo_mes
        return {
            "nome": f"Energia solar por assinatura (desconto de {desconto * 100:.0f}%)",
            "descricao": "Fonte renovável (solar fotovoltaica) por geração compartilhada, sem obra e sem equipamento.",
            "kwh_mes": base,
            "custo_mes": custo_mes,
            "custo_ano": custo_mes * MESES_ANO,
            "economia_mes": economia_mes,
            "economia_ano": economia_mes * MESES_ANO,
            "emissao_evitada_kg_ano": 0.0,
            "desconto": desconto,
        }

    def comparar(self, residencia):
        assinatura = self.dados.assinatura()
        return {
            "base": self.cenario_base(residencia),
            "eficiencia": self.cenario_eficiencia(residencia),
            "assinatura_min": self.cenario_assinatura(residencia, assinatura["desconto_minimo"]),
            "assinatura_max": self.cenario_assinatura(residencia, assinatura["desconto_maximo"]),
        }


def formatar_numero(valor, casas=2):
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_moeda(valor):
    return f"R$ {formatar_numero(valor, 2)}"
