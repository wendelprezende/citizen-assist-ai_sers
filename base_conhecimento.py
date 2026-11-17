import json
from orientacao import Orientacao

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ç": "c"}

def normalizar(texto):
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in "?!.,;:()-/\"'":
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "

class BaseConhecimento:
    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []

    def carregar(self):
        self.orientacoes = []
        try:
            with open(self.caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            print("Base de conhecimento não encontrada.")
            return
        except json.JSONDecodeError:
            print("Base de conhecimento corrompida.")
            return

        if not isinstance(dados, list):
            print("Base de conhecimento corrompida.")
            return

        for dicionario in dados:
            try:
                orientacao = Orientacao(**dicionario)
            except TypeError:
                print("Registro inválido ignorado (campos incorretos)")
                continue
            self.orientacoes.append(orientacao)

    def categorias(self):
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria == categoria:
                lista.append(orientacao)
        return lista

    def pontuar(self, orientacao, pergunta):
        pontos = 0
        for palavra_chave in orientacao.palavras_chave:
            if normalizar(palavra_chave) in pergunta:
                pontos += 3

        titulo = normalizar(orientacao.titulo)
        for palavra in set(pergunta.split()):
            if len(palavra) >= 4 and f" {palavra} " in titulo:
                pontos += 1
        return pontos

    def buscar(self, pergunta):
        pergunta = normalizar(pergunta)
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(orientacao, pergunta)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda resultado: resultado[0], reverse=True)
        return resultados