from energia import DadosEnergia, CalculadoraEnergia, Equipamento, Residencia


def aproximado(a, b, margem=0.01):
    return abs(a - b) <= margem


def montar_residencia(dados, tipo, moradores, ids, minutos_banho=10):
    residencia = Residencia(tipo, moradores)
    for item in dados.catalogo():
        if item["id"] not in ids:
            continue
        horas = item["horas_dia"]
        if item["id"] == "chuveiro":
            horas = minutos_banho * moradores / 60
        residencia.adicionar(Equipamento(
            item["id"], item["nome"], item["potencia_w"], horas, item["dias_mes"],
            item["kwh_mes_fixo"], item.get("fator_uso", 1.0)))
    return residencia


def main():
    dados = DadosEnergia("data/energia_dados.json")
    if not dados.carregar():
        return
    erros = 0

    def conferir(descricao, obtido, esperado, margem=0.01):
        nonlocal erros
        ok = aproximado(obtido, esperado, margem)
        if not ok:
            erros += 1
        print(f" {'OK  ' if ok else 'ERRO'} {descricao}: obtido {obtido:.4f}, esperado {esperado:.4f}")

    print("Conferência com a tabela de consumo (Eletrobras):")
    tabela = {"chuveiro": 70.0, "ar_condicionado": 120.0, "ventilador": 28.8,
              "computador": 10.8, "tv": 16.5, "ferro": 12.0, "lavadora": 6.0}
    for item in dados.catalogo():
        if item["id"] in tabela:
            horas = 40 / 60 if item["id"] == "chuveiro" else item["horas_dia"]
            equipamento = Equipamento(item["id"], item["nome"], item["potencia_w"], horas,
                                      item["dias_mes"], item["kwh_mes_fixo"], item.get("fator_uso", 1.0))
            conferir(item["nome"], equipamento.consumo_mensal_kwh(), tabela[item["id"]])

    print("\nTarifa (R$/kWh):")
    conferir("bandeira verde", dados.tarifa("verde").valor_kwh(), 0.78938, 0.00001)
    conferir("bandeira amarela", dados.tarifa("amarela").valor_kwh(), 0.80823, 0.00001)
    conferir("100 kWh na verde", dados.tarifa("verde").custo(100), 78.938)

    print("\nCenários (família de 4 pessoas, conta de verão):")
    calculadora = CalculadoraEnergia(dados, "verde")
    familia = montar_residencia(dados, "familia", 4,
                                ["chuveiro", "geladeira_2p", "computador", "tv", "ar_condicionado"], 10)
    resultado = calculadora.comparar(familia)
    conferir("consumo base (70+55+10,8+16,5+120 kWh)", resultado["base"]["kwh_mes"], 272.3)
    conferir("custo base por mês", resultado["base"]["custo_mes"], 272.3 * 0.78938)
    conferir("assinatura 10% economiza 10% do custo",
             resultado["assinatura_min"]["economia_mes"], resultado["base"]["custo_mes"] * 0.10)
    conferir("assinatura 20% economiza 20% do custo",
             resultado["assinatura_max"]["economia_mes"], resultado["base"]["custo_mes"] * 0.20)
    ventilador = 120 * 8 * 30 / 1000 * 0.5
    eficiente = 70 * 0.75 + 55 + 10.8 * 0.85 + 16.5 * 0.85 + 120 * 0.5 + ventilador
    conferir("consumo no cenário de eficiência", resultado["eficiencia"]["kwh_mes"], eficiente)

    print(f"\nResultado: {'tudo certo' if erros == 0 else str(erros) + ' erro(s)'}")


if __name__ == "__main__":
    main()
