import json
from collections import Counter

CAMPOS = ["id", "categoria", "titulo", "palavras_chave", "resposta",
          "documentos", "onde", "fonte", "verificado_em"]

with open("data/base_conhecimento.json", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

problemas = []

if len(dados) < 10:
    problemas.append(f"Só há {len(dados)} orientações (mínimo 10).")

categorias = set()
contagem = Counter()
ids = []
for registro in dados:
    rotulo = f"id {registro.get('id', '?')}"
    faltando = [c for c in CAMPOS if c not in registro]
    if faltando:
        problemas.append(f"{rotulo}: faltam os campos {faltando}.")
        continue
    ids.append(registro["id"])
    categorias.add(registro["categoria"])
    if len(registro["palavras_chave"]) < 3:
        problemas.append(f"{rotulo}: menos de 3 palavras-chave.")
    for palavra in registro["palavras_chave"]:
        contagem[palavra] += 1
        if palavra != palavra.lower() or "." in palavra:
            problemas.append(f"{rotulo}: palavra-chave '{palavra}' com maiúscula ou ponto.")
    if not registro["fonte"].startswith("https://"):
        problemas.append(f"{rotulo}: fonte sem https://.")
    if not registro["documentos"]:
        problemas.append(f"{rotulo}: lista de documentos vazia.")

if len(categorias) < 3:
    problemas.append(f"Só há {len(categorias)} categorias (mínimo 3).")
if len(ids) != len(set(ids)):
    problemas.append("Há ids repetidos.")
for palavra, vezes in contagem.items():
    if vezes > 1:
        problemas.append(f"Palavra-chave repetida entre orientações: '{palavra}'.")

print(f"Orientações: {len(dados)} | Categorias: {sorted(categorias)}")
if problemas:
    print("PROBLEMAS ENCONTRADOS:")
    for problema in problemas:
        print(" -", problema)
else:
    print("Base válida: tudo conforme o documento.")
