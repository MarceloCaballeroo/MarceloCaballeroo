"""Genera dark_mode.svg y light_mode.svg: retrato ASCII + datos del perfil + estadisticas vivas de GitHub.

Uso: GITHUB_TOKEN=... python build.py
Solo usa la biblioteca estandar. Sin token, las estadisticas quedan como "n/d".
"""
import json
import os
import urllib.request
from html import escape

USER = "MarceloCaballeroo"
FONT = 14
LINE = 18
ASCII_X = 15
ASCII_FONT = 12
ASCII_LINE = 14
INFO_X = 570
WIDTH = 1040

PROFILE = [
    ("Rol", "Estudiante de Ingeniería en Informática"),
    ("Hoy", "Práctica en Auditoría y Control Interno,"),
    ("", "LATAM Airlines"),
    ("Antes", "Endpoint Security Specialist L2, IBM Chile"),
    ("Ubicación", "Santiago, Chile"),
    ("Foco", "Ciberseguridad · IA · Cloud"),
    None,
    ("SECTION", "Stack"),
    ("Lenguajes", "Python, TypeScript, Java, C#, SQL, Bash"),
    ("Backend", "Spring Boot, Next.js, Supabase, Firebase"),
    ("Cloud", "AWS, Azure, GCP, Amazon Bedrock"),
    ("Seguridad", "CrowdStrike, Trend Micro, Defender"),
    ("IA", "Gemini, OpenAI, Anthropic, OpenCode, Grok"),
    None,
    ("SECTION", "Comunidad y logros"),
    ("Comunidad", "AWS Cloud Club Captain (Gold), MLSA"),
    ("Logros", "1º CTF Intercede, 9º Llaitún 2024"),
    ("Certificaciones", "22 verificadas en Credly"),
    None,
    ("SECTION", "Contacto"),
    ("Portafolio", "marcelocaballero.me"),
    ("LinkedIn", "marcelo-caballero-olave"),
    ("Credly", "marcelo-ignacio-caballero-olave"),
    None,
    ("SECTION", "GitHub"),
    ("Repos", "{repos}"),
    ("Estrellas", "{stars}"),
    ("Commits", "{commits}"),
    ("Seguidores", "{followers}"),
]

THEMES = {
    "dark_mode": dict(bg="#161b22", ascii="#c9d1d9", key="#ffa657", val="#a5d6ff", sec="#3fb950", cc="#616e7f"),
    "light_mode": dict(bg="#f6f8fa", ascii="#24292f", key="#953800", val="#0a3069", sec="#116329", cc="#6e7781"),
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
    }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
  }
}
"""


def stars(token):
    """Suma de estrellas de los repositorios publicos propios (REST: el token de Actions solo ve este repo en GraphQL)."""
    total, page = 0, 1
    while True:
        req = urllib.request.Request(
            "https://api.github.com/users/%s/repos?type=owner&per_page=100&page=%d" % (USER, page),
            headers={"Authorization": "Bearer " + token, "User-Agent": "profile-readme"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            repos = json.load(r)
        total += sum(x["stargazers_count"] for x in repos if not x["fork"])
        if len(repos) < 100:
            return total
        page += 1


def stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    na = {"repos": "n/d", "stars": "n/d", "commits": "n/d", "followers": "n/d"}
    if not token:
        return na
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "User-Agent": "profile-readme"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            u = json.load(r)["data"]["user"]
    except Exception as e:  # noqa: BLE001
        print("No se pudieron leer las estadisticas:", e)
        return na
    cc = u["contributionsCollection"]
    return {
        "repos": str(u["repositories"]["totalCount"]),
        "stars": str(stars(token)),
        "commits": str(cc["totalCommitContributions"] + cc["restrictedContributionsCount"]) + " (último año)",
        "followers": str(u["followers"]["totalCount"]),
    }


def info_lines(st):
    out = [("head", "marcelo@caballero")]
    out.append(("rule", "-" * 18))
    for item in PROFILE:
        if item is None:
            out.append(("blank", ""))
        elif item[0] == "SECTION":
            out.append(("sec", "— " + item[1] + " " + "—" * max(2, 42 - len(item[1]))))
        else:
            out.append(("kv", item[0], item[1].format(**st)))
    return out


def render(name, theme, ascii_rows, lines):
    height = 30 + max(len(ascii_rows) * ASCII_LINE, len(lines) * LINE)
    p = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',monospace" '
        'width="%dpx" height="%dpx" font-size="%dpx" role="img" aria-label="Perfil de Marcelo Caballero Olave">' % (WIDTH, height, FONT),
        "<style>@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';font-display:swap;size-adjust:109%%}"
        ".k{fill:%s}.v{fill:%s}.s{fill:%s}.c{fill:%s}text,tspan{white-space:pre}</style>" % (theme["key"], theme["val"], theme["sec"], theme["cc"]),
        '<rect width="%dpx" height="%dpx" fill="%s" rx="15"/>' % (WIDTH, height, theme["bg"]),
    ]
    off = (height - 30 - len(ascii_rows) * ASCII_LINE) // 2
    p.append('<text fill="%s" font-size="%dpx" aria-hidden="true">' % (theme["ascii"], ASCII_FONT))
    for i, row in enumerate(ascii_rows):
        p.append('<tspan x="%d" y="%d">%s</tspan>' % (ASCII_X, 30 + off + i * ASCII_LINE, escape(row)))
    p.append("</text>")
    off = (height - 30 - len(lines) * LINE) // 2
    p.append('<text fill="%s">' % theme["ascii"])
    for i, ln in enumerate(lines):
        y = 30 + off + i * LINE
        kind = ln[0]
        if kind == "head":
            p.append('<tspan x="%d" y="%d" class="s">%s</tspan>' % (INFO_X, y, escape(ln[1])))
        elif kind == "rule":
            p.append('<tspan x="%d" y="%d" class="c">%s</tspan>' % (INFO_X, y, ln[1]))
        elif kind == "sec":
            p.append('<tspan x="%d" y="%d" class="c">%s</tspan>' % (INFO_X, y, escape(ln[1])))
        elif kind == "kv":
            key, val = ln[1], ln[2]
            if key:
                p.append('<tspan x="%d" y="%d" class="k">%s</tspan><tspan class="c">: </tspan><tspan class="v">%s</tspan>' % (INFO_X, y, escape(key), escape(val)))
            else:
                p.append('<tspan x="%d" y="%d" class="v">  %s</tspan>' % (INFO_X, y, escape(val)))
    p.append("</text></svg>")
    open(name + ".svg", "w", encoding="utf-8", newline="\n").write("\n".join(p) + "\n")


def main():
    st = stats()
    lines = info_lines(st)
    for name, theme in THEMES.items():
        rows = open("ascii_%s.txt" % name.split("_")[0], encoding="utf-8").read().rstrip("\n").split("\n")
        render(name, theme, rows, lines)
    print("Generado:", st)


if __name__ == "__main__":
    main()
