"""Coleta diária da lotação prisional publicada pela SAP-SP.

Baixa o arquivo pop-pri.js da página Unidades Prisionais, lê capacidade e
população de cada pavilhão do catálogo e acrescenta uma linha por pavilhão em
data/historico.json, com a data de população informada pela SAP. Guarda o
arquivo original do dia em data/bruto/. Se a SAP ainda não mudou a data, não
altera nada.

Uso: python3 coleta/atualizar.py [arquivo_local_pop-pri.js]
"""
import datetime
import json
import os
import re
import sys
import urllib.request

URL = "https://www1.sap.sp.gov.br/sp/js/pop-pri.js"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "data")
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}
LISTADAS = [22, 104, 32, 41, 42, 47, 59, 142, 145, 158, 161, 164, 168, 173, 175]
BRT = datetime.timezone(datetime.timedelta(hours=-3))


def resumo_saida(texto):
    """Escreve no resumo do GitHub Actions, quando houver."""
    print(texto)
    destino = os.environ.get("GITHUB_STEP_SUMMARY")
    if destino:
        with open(destino, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def baixar():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (painel de lotacao; coleta diaria)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def ler_variaveis(texto):
    vals = {}
    for linha in texto.splitlines():
        m = re.match(r'\s*var\s+([A-Za-z_]\w*)\s*=\s*(?:"([^"]*)"|([^;\s/]*))', linha)
        if m:
            vals[m.group(1)] = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
    return vals


def num(v):
    d = re.sub(r"\D", "", v or "")
    return int(d) if d else None


def main():
    bruto = open(sys.argv[1], "rb").read() if len(sys.argv) > 1 else baixar()
    texto = bruto.decode("utf-8", errors="replace")
    vals = ler_variaveis(texto)

    dm = re.match(r"(\d{1,2})/([a-zç]{3})", vals.get("datapoptotal2", "").lower())
    if not dm:
        resumo_saida(f"ERRO: data da população (datapoptotal2) ausente ou ilegível: {vals.get('datapoptotal2')!r}")
        sys.exit(2)
    dia, mes = int(dm.group(1)), MESES[dm.group(2)]
    hoje = datetime.datetime.now(BRT).date()
    ano = hoje.year - 1 if mes > hoje.month else hoje.year
    data = datetime.date(ano, mes, dia).isoformat()

    cat = json.load(open(os.path.join(DADOS, "catalogo.json"), encoding="utf-8"))["rows"]
    caminho_hist = os.path.join(DADOS, "historico.json")
    hist = json.load(open(caminho_hist, encoding="utf-8"))["rows"]
    if any(r["d"] == data for r in hist):
        resumo_saida(f"Sem novidade: a população de {data} já está registrada.")
        return

    novos, faltando = [], []
    for c in cat:
        cap, pop = num(vals.get(c["var_capacidade"])), num(vals.get(c["var_populacao"]))
        if cap is None or pop is None:
            faltando.append(c["id"])
            continue
        novos.append({"d": data, "i": c["id"], "c": cap, "p": pop})
    if len(novos) < 0.9 * len(cat):
        resumo_saida(f"ERRO: só {len(novos)} de {len(cat)} pavilhões encontrados; nada foi gravado. Faltando: {faltando}")
        sys.exit(3)

    os.makedirs(os.path.join(DADOS, "bruto"), exist_ok=True)
    with open(os.path.join(DADOS, "bruto", f"pop-pri_{data}.js"), "wb") as f:
        f.write(bruto)
    with open(caminho_hist, "w", encoding="utf-8") as f:
        json.dump({"rows": hist + novos}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(DADOS, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"data_sap": data, "coletado_em": datetime.datetime.now(BRT).isoformat(timespec="minutes")}, f)

    # Resumo para quem acompanha a coleta
    cad = {c["id"]: c for c in cat}

    def conta(r):
        return cad[r["i"]]["situacao"] == "Em funcionamento" or r["p"] > 0

    def unidades(rows):
        u = {}
        for r in rows:
            if r["i"] not in cad or not conta(r):
                continue
            k = cad[r["i"]]["unidade_id"]
            a = u.setdefault(k, [0, 0, cad[r["i"]]["unidade"], cad[r["i"]]["raj4"]])
            a[0] += r["c"]
            a[1] += r["p"]
        return u

    def taxa(c, p):
        return f"{p / c * 100:.1f}%".replace(".", ",") if c else "—"

    def sa(rows, sexo):
        rs = [r for r in rows if r["i"] in cad and cad[r["i"]]["semiaberto"] and cad[r["i"]]["sexo"] == sexo and cad[r["i"]]["raj4"] and conta(r)]
        return taxa(sum(r["c"] for r in rs), sum(r["p"] for r in rs))

    ultima = max(r["d"] for r in hist)
    ant = [r for r in hist if r["d"] == ultima]
    U0, U1 = unidades(ant), unidades(novos)
    acima = lambda U, k: k in U and U[k][0] and U[k][1] > 1.375 * U[k][0]
    passou = sorted(v[2] for k, v in U1.items() if v[3] and acima(U1, k) and not acima(U0, k))
    voltou = sorted(v[2] for k, v in U0.items() if v[3] and acima(U0, k) and k in U1 and not acima(U1, k))
    conhecidas = {c["var_populacao"] for c in cat}
    novas_vars = sorted(k for k in vals if ("cap" + k) in vals and k not in conhecidas)
    linhas = [
        f"## População de {data} registrada",
        f"- Semiaberto masculino, 4ª RAJ: {sa(novos, 'Masculino')} (antes: {sa(ant, 'Masculino')})",
        f"- Semiaberto feminino, 4ª RAJ: {sa(novos, 'Feminino')} (antes: {sa(ant, 'Feminino')})",
        f"- Todas as unidades do Estado: {taxa(sum(v[0] for v in U1.values()), sum(v[1] for v in U1.values()))}",
        f"- Unidades indicadas pelo DEECRIM acima de 137,5%: {sum(1 for k in LISTADAS if acima(U1, k))} de {len(LISTADAS)}",
    ]
    if passou:
        linhas.append(f"- Passaram de 137,5% (4ª RAJ): {', '.join(passou)}")
    if voltou:
        linhas.append(f"- Voltaram abaixo de 137,5% (4ª RAJ): {', '.join(voltou)}")
    if faltando:
        linhas.append(f"- ATENÇÃO, pavilhões sem número na SAP: {faltando}")
    if novas_vars:
        linhas.append(f"- ATENÇÃO, possíveis unidades ou pavilhões novos (fora do catálogo): {novas_vars}")
    resumo_saida("\n".join(linhas))


if __name__ == "__main__":
    main()
