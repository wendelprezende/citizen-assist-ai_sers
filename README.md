# Citizen Assist AI — Energia

Extensão do **Citizen Assist AI**, assistente de terminal em Python que orienta quem acaba de completar 18 anos. Nesta versão (Global Solution 2026.2, SERS), o assistente ganhou o tema **conta de luz**: explica a tarifa, calcula o consumo da casa e compara formas de reduzir o custo.

> O assistente **não é um canal oficial**. Os resultados são **estimativas**, não garantem economia e não incluem impostos (ICMS, PIS/Cofins) nem iluminação pública. Não digite dados pessoais.

## 1. Integrantes

| Nome | RM |
|---|---|
| Wendel Rezende | 573126 |
| Daniel Alejandro | 573075 |
| Arthur Araújo | 573308 |

## 2. Público e necessidade

- **Público:** jovens de 18 anos, em São Paulo (capital, distribuidora **Enel SP**), que passam a administrar a própria conta de luz, morando **sozinhos ou com a família**.
- **Necessidade:** entender a conta, saber o que mais pesa nela e decidir como reduzir o custo sem depender de promessas de economia.
- **Caso central:** o **chuveiro elétrico**, maior consumidor individual da casa-modelo.

## 3. O que o assistente faz

- **Opções 1 a 4 do menu:** perguntas por texto, navegação por categorias, indicadores e exportação CSV (herdados do projeto de PCP).
- **Orientações de energia (ids 11 a 16, categoria "Energia e sustentabilidade"):** tarifa, bandeiras, chuveiro, stand-by/geladeira/ar-condicionado, energia solar por assinatura e Tarifa Social. Cada resposta mostra fonte e data de verificação.
- **Opção 5 — Calcular consumo e economia de energia:** pergunta se mora sozinho ou em família, minutos de banho, aparelhos, horas de uso e bandeira tarifária. Mostra consumo estimado, maiores consumidores, comparação de cenários em 12 meses, premissas com fontes e um aviso final.

## 4. Como executar

Requisitos: Python 3.10 ou superior. Não há bibliotecas externas.

```bash
python main.py            # assistente
python teste_energia.py   # confere os cálculos (esperado: "Resultado: tudo certo")
python validar.py         # confere a base de orientações (esperado: "Base válida")
```

## 5. Estrutura

```
main.py                 ponto de entrada e menu
assistente.py           conversa com o usuário, fluxo da opção 5, histórico e indicadores
energia.py              cálculo: tarifa, equipamento, residência e cenários
orientacao.py           classe Orientacao
base_conhecimento.py    leitura da base e busca por palavras-chave
teste_energia.py        testes dos cálculos
validar.py              validação da base de orientações
data/base_conhecimento.json   16 orientações com fonte e data
data/energia_dados.json       dados de energia, com origem, tipo e fonte
data/historico.json           histórico de atendimentos (começa vazio)
```

O cálculo (`energia.py`) não usa `input` nem `print`; a conversa fica em `assistente.py`. Os números ficam em `energia_dados.json`, então mudar uma tarifa não exige mexer no código.

## 6. Dados, origem e premissas

Cada dado está marcado como **oficial**, **estimado** ou **hipótese** em `data/energia_dados.json`.

| Dado | Valor | Tipo | Origem |
|---|---|---|---|
| Tarifa Enel SP, B1 convencional | R$ 0,78938/kWh (TUSD 0,47242 + TE 0,31696), sem tributos | oficial | [Enel SP](https://www.enel.com.br/pt-saopaulo/Para_Voce/tarifa-energia-eletrica.html); Resolução Homologatória ANEEL nº 3.596/2026; vigência 04/07/2026 a 03/07/2027 |
| Bandeiras (R$ por 100 kWh) | verde 0; amarela 1,885; vermelha 1 4,463; vermelha 2 7,877 | oficial | [ANEEL](https://www.gov.br/aneel/pt-br/assuntos/tarifas/bandeiras-tarifarias); vigente em novembro/2026: verde |
| Fator de emissão | 0,0247 kg CO2/kWh | oficial, média calculada pelo grupo | MCTI (fatores mensais do SIN, jan–abr/2025), via [Canal Solar](https://canalsolar.com.br/emissoes-de-co%e2%82%82-geracao-eletrica-mcti/) |
| Potência e uso dos aparelhos | chuveiro 3.500 W, geladeira 2 portas 55 kWh/mês, ar-condicionado 7.500 BTU, computador, TV etc. | estimado | [Tabela de consumo (fonte original: Eletrobras)](https://igce.rc.unesp.br/Home/ComissaoSupervisora-old/ConservacaodeEnergiaCICE/tabela_consumo.pdf) |
| Minutos de banho por pessoa | 10 | estimado | Tabela: 40 min/dia na casa ÷ 4 pessoas (premissa do grupo) |
| Redução do tempo de banho | 25% | hipótese do cenário | Escolha do grupo; pode ser mudada |
| Redução do stand-by | até 15% do consumo de TV e computador | limite superior da fonte | [Cemig / Agência Minas](https://www.agenciaminas.mg.gov.br/news/pdf/120522.pdf) |
| Ar-condicionado trocado por ventilador | metade das horas | hipótese do cenário | Escolha do grupo |
| Desconto da assinatura solar | 10% a 20% | estimado | Imprensa: [InfoMoney](https://www.infomoney.com.br/?p=2072005), [Eixos](https://eixos.com.br/?p=71033) |
| Conta mínima citada para assinatura | R$ 200 a 300 por mês | estimado | [Eu Quero Investir](https://euqueroinvestir.com/educacao-financeira/energia-por-assinatura-conta-mais-barata), [Agrolink](https://www.agrolink.com.br/noticias/como-funciona-a-assinatura-de-energia-solar_453010.html) |

Dados consultados em 16/11/2026. As fontes foram verificadas pelo grupo.

## 7. Cálculos

```
kWh/mês   = potência (W) × horas/dia × dias/mês ÷ 1000 × fator de uso
custo/mês = kWh × (tarifa + bandeira ÷ 100)
chuveiro  = 3.500 W × (pessoas × minutos ÷ 60) h/dia × 30 dias ÷ 1000
CO2 evitado (kg/ano) = kWh economizados no ano × 0,0247
```

- **Período de referência:** 12 meses, com o mesmo consumo mensal todos os meses (premissa; na prática varia com o clima).
- **Geladeira:** usa o consumo mensal fixo da tabela, porque funciona de forma intermitente.
- **Ar-condicionado:** a tabela informa 120 kWh/mês. Com 1.000 W × 8 h × 30 dias o cálculo dá 240 kWh, então o grupo adotou **fator de uso 0,5** (o compressor não trabalha o tempo todo). Esse fator foi **deduzido pelo grupo** a partir da tabela.
- **Validação:** `teste_energia.py` compara os resultados com os valores da tabela (chuveiro 70, ar 120, ventilador 28,8, computador 10,8, TV 16,5, ferro 12, lavadora 6 kWh/mês) e com a tarifa.

## 8. Comparação de alternativas para a mesma necessidade

**Necessidade:** reduzir a conta de luz da casa em 12 meses, na mesma tarifa. Duas alternativas são comparadas ao uso atual.

| Alternativa | O que muda | Natureza |
|---|---|---|
| A. Eficiência energética | Banho 25% mais curto, stand-by desligado e ventilador no lugar de metade do ar-condicionado | Hábitos, sem investimento |
| B. Energia solar por assinatura | Parte da energia vem de uma usina solar fotovoltaica, com desconto de 10% a 20% sobre a conta | **Fonte renovável**, sem obra nem equipamento |

### Casa-modelo A: família de 4 pessoas (bandeira verde)

Aparelhos: chuveiro, geladeira 2 portas, computador, TV e ar-condicionado. Consumo: **272,3 kWh/mês**.

| Cenário | Consumo/mês | Conta/mês | Economia/ano |
|---|---|---|---|
| Uso atual | 272,3 kWh | R$ 214,95 | — |
| A. Eficiência | 205,1 kWh | R$ 161,91 | R$ 636,51 (24,7%) |
| B. Assinatura solar | 272,3 kWh | R$ 171,96 a R$ 193,45 | R$ 257,94 a R$ 515,88 |

Sensibilidade à bandeira, família de 4 pessoas:

| Bandeira | Conta/mês | Economia/ano (eficiência) | Economia/ano (assinatura) |
|---|---|---|---|
| Verde | R$ 214,95 | R$ 636,51 | R$ 257,94 a 515,88 |
| Amarela | R$ 220,08 | R$ 651,71 | R$ 264,10 a 528,19 |
| Vermelha 1 | R$ 227,10 | R$ 672,50 | R$ 272,52 a 545,04 |
| Vermelha 2 | R$ 236,40 | R$ 700,02 | R$ 283,68 a 567,35 |

### Casa-modelo B: morando sozinho (bandeira verde)

Aparelhos: chuveiro, geladeira 2 portas e computador. Consumo: **83,3 kWh/mês**, conta de **R$ 65,76**. Eficiência: R$ 56,79/ano (7,2%). Assinatura: R$ 78,91 a 157,81/ano, mas com conta abaixo da mínima citada (R$ 200 a 300), então o assistente avisa que a assinatura pode não compensar.

Os valores em reais são calculados **sem impostos**. Tributos e iluminação pública aumentam a conta real.

### Justificativas

- **Custo:** a eficiência não exige investimento e dá a maior economia estimada na casa de 4 pessoas. A assinatura também não exige investimento, mas depende do contrato e da conta mínima.
- **Viabilidade:** a eficiência depende de mudar hábitos (principalmente o banho). A assinatura depende de a empresa atender a região, do valor da conta e de regras que a ANEEL ainda discute (**risco regulatório**).
- **Impacto ambiental:** a eficiência evita cerca de **19,9 kg de CO2 por ano** na casa de 4 pessoas. É pouco, porque a matriz elétrica brasileira já é majoritariamente renovável (0,0247 kg CO2/kWh). Na assinatura solar o assistente **não calcula** redução de CO2: o ganho dela é principalmente financeiro, e a conta continua usando a mesma energia da rede.

## 9. Integração com as respostas do assistente

- As orientações 11 a 16 trazem fonte e data de verificação, como as demais.
- A opção 5 usa os dados de `energia_dados.json` e mostra, ao fim, as **premissas e fontes** com a marcação **[oficial]** ou **[estimado]**, além dos **pontos de atenção** (conta mínima, risco regulatório, impostos não incluídos) e do aviso de que o assistente não é canal oficial.
- Cada cálculo é registrado no histórico como origem `energia`, sem dados pessoais.

## 10. Limitações

- Resultados são **estimativas**; a potência real está na etiqueta de cada aparelho.
- Não inclui ICMS, PIS/Cofins nem iluminação pública.
- Considera um consumo igual em todos os meses.
- O fator de uso do ar-condicionado e as hipóteses dos cenários foram escolhidos pelo grupo.
- O desconto da assinatura vem de reportagens e varia por empresa e contrato.
- Vale só para a Enel SP, classe residencial convencional, e para a vigência da tarifa indicada.
- Nenhuma economia é garantida.

## 11. Contribuição de cada integrante

- **Wendel Rezende:** assistente.py, main.py, base_conhecimento.py, data/ e README.md
- **Daniel Alejandro:** Roteiro do vídeo, orientacao.py e validar.py
- **Arthur Araújo:** teste_energia.py e energia.py

## 12. Referências

- Enel SP — Tarifas: https://www.enel.com.br/pt-saopaulo/Para_Voce/tarifa-energia-eletrica.html
- Enel SP — Bandeira tarifária: https://www.enel.com.br/pt-saopaulo/Corporativo_e_Governo/Bandeira_Tarifaria.html
- Enel SP — Tarifa Social: https://www.enel.com.br/pt-saopaulo/Para_Voce/Tarifa_Social_Baixa_Renda.html
- ANEEL — Bandeiras tarifárias: https://www.gov.br/aneel/pt-br/assuntos/tarifas/bandeiras-tarifarias
- Lei nº 14.300/2022: https://www2.camara.leg.br/legin/fed/lei/2022/lei-14300-6-janeiro-2022-792217-publicacaooriginal-164335-pl.html
- Cemig / Agência Minas (dicas de economia): https://www.agenciaminas.mg.gov.br/news/pdf/120522.pdf
- Tabela de consumo de aparelhos: https://igce.rc.unesp.br/Home/ComissaoSupervisora-old/ConservacaodeEnergiaCICE/tabela_consumo.pdf
- Fator de emissão (MCTI): https://canalsolar.com.br/emissoes-de-co%e2%82%82-geracao-eletrica-mcti/
- Assinatura solar: https://www.infomoney.com.br/?p=2072005 · https://eixos.com.br/?p=71033 · https://euqueroinvestir.com/educacao-financeira/energia-por-assinatura-conta-mais-barata · https://www.agrolink.com.br/noticias/como-funciona-a-assinatura-de-energia-solar_453010.html
- Regras da geração compartilhada: https://canalsolar.com.br/aneel-mudancas-regras-geracao-compartilhada/

## 13. Entrega

- Vídeo (YouTube, não listado, até 3 min): https://youtu.be/GCGIqloKG8I
