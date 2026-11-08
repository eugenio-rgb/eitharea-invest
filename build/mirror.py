"""Descarga el sitio EITHAREA Invest desde el origen en Wix y lo prepara para GitHub Pages.
El contenido se edita en el sitio de Wix (origen); este script lo copia, ajusta y publica en invest.eitharea.com."""
import os, re, urllib.request

ORIGIN = "https://headless-euduymuhggp-eugenio64-1409.wix-site-host.com/"
DOMAIN = "https://invest.eitharea.com/"
OUT = "public"

def get(path):
    req = urllib.request.Request(ORIGIN + path, headers={"User-Agent": "eitharea-invest-mirror", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def save(path, data):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)

# Descubre las páginas siguiendo los enlaces internos desde las portadas
pages, queue, assets = [], ["index.html", "es/index.html", "capitulo-1.html"], set()
while queue:
    p = queue.pop(0)
    if p in pages:
        continue
    try:
        html = get(p).decode("utf-8")
    except Exception as e:
        print("omitida", p, e)
        continue
    pages.append(p)
    base = os.path.dirname(p)
    for href in re.findall(r'(?:href|src)="([^"#?]+)"', html):
        if href.startswith(("http", "mailto:", "tel:", "//", "data:")):
            continue
        target = os.path.normpath(os.path.join(base, href.lstrip("/") if href.startswith("/") else href)).replace("\\", "/")
        if href.startswith("/"):
            target = href.lstrip("/")
        if target.startswith(".."):
            continue
        if target.endswith(".html") and target not in pages and target not in queue:
            queue.append(target)
        elif target.startswith("assets/"):
            assets.add(target)
    html = re.sub(r'<script id="wix-site-script"[^>]*></script>\n?', "", html)
    html = html.replace('hreflang="en" href="/', 'hreflang="en" href="' + DOMAIN).replace('hreflang="es" href="/', 'hreflang="es" href="' + DOMAIN)
    if '<link rel="canonical"' not in html:
        html = html.replace("</title>\n", '</title>\n<link rel="canonical" href="' + DOMAIN + p + '">\n', 1)
    save(p, html.encode("utf-8"))

for a in sorted(assets):
    save(a, get(a))

save("CNAME", b"invest.eitharea.com\n")
save("robots.txt", ("User-agent: *\nAllow: /\n\nSitemap: " + DOMAIN + "sitemap.xml\n").encode())
urls = "".join("  <url><loc>" + DOMAIN + p + "</loc></url>\n" for p in sorted(pages))
save("sitemap.xml", ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n").encode())

idx = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
head = re.sub(r"<title>[^<]*</title>", "<title>Page not found | EITHAREA</title>", idx[: idx.index("<main>") + 6])
tail = idx[idx.index("</main>"):]
body = ('\n<div class="wrap page-hero"><h1>Page not found · Página no encontrada</h1><p class="lead">'
        '<a href="/opportunities.html">See opportunities</a> · <a href="/es/oportunidades.html">Ver oportunidades</a></p></div>\n')
nf = head + body + tail
nf = re.sub(r'(href|src)="(?!https?:|//|/|mailto:|tel:|#)', r'\1="/', nf)
save("404.html", nf.encode("utf-8"))
print(len(pages), "páginas,", len(assets), "archivos de assets")
