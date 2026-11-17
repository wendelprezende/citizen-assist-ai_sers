from base_conhecimento import BaseConhecimento
from assistente import Assistente
from energia import DadosEnergia

base = BaseConhecimento("data/base_conhecimento.json")
base.carregar()

dados_energia = DadosEnergia("data/energia_dados.json")
if not dados_energia.carregar():
    dados_energia = None

assistente = Assistente("Citizen Assist AI", base, dados_energia=dados_energia)

print(f"=== {assistente.nome} ===")
print("Este assistente NÃO é um canal oficial. Não digite dados pessoais.")

while True:
    print("\nMenu principal:")
    print(" 1 - Fazer uma pergunta")
    print(" 2 - Navegar por categorias")
    print(" 3 - Ver indicadores")
    print(" 4 - Exportar atendimentos (CSV)")
    print(" 5 - Calcular consumo e economia de energia")
    print(" 0 - Sair")
    opcao = assistente.ler_opcao(5)

    if opcao == 1:
        assistente.perguntar()
    elif opcao == 2:
        assistente.navegar()
    elif opcao == 3:
        assistente.indicadores()
    elif opcao == 4:
        assistente.exportar_csv()
    elif opcao == 5:
        assistente.calcular_energia()
    else:
        break

assistente.pedir_nota_facilidade()
assistente.exportar_csv()
print("Obrigado por usar o Citizen Assist AI!")
