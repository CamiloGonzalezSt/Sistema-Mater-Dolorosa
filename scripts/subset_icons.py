"""Regenera el subset de Tabler Icons con solo los íconos usados en las plantillas.

Reduce el CSS (~247 KB) y la fuente (~820 KB) a unos pocos KB.

Uso:
    python scripts/subset_icons.py
    # luego, para subsetear la fuente (requiere fonttools + brotli):
    #   python -m fontTools.subset static/css/fonts/tabler-icons.woff2 \
    #     --unicodes=<lista> --flavor=woff2 \
    #     --output-file=static/css/fonts/tabler-icons.subset.woff2
    # El script imprime la lista de unicodes lista para copiar.

Si agregas un ícono nuevo en una plantilla, añádelo a USADOS y vuelve a correr.
"""
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSS = BASE / 'static' / 'css' / 'tabler-icons.min.css'
FONT_SRC = BASE / 'static' / 'css' / 'fonts' / 'tabler-icons.woff2'
FONT_OUT = BASE / 'static' / 'css' / 'fonts' / 'tabler-icons.subset.woff2'

# Íconos usados en templates/ (mantener sincronizado con las plantillas)
USADOS = [
    'bell', 'book', 'book-2', 'calendar-event', 'cash', 'chevron-down',
    'clipboard-check', 'folder', 'layout-dashboard', 'login-2', 'logout',
    'mail', 'menu-2', 'notebook', 'school', 'settings', 'star', 'users',
    'wallet',
]


def main():
    texto = CSS.read_text(encoding='utf-8')
    reglas, codepoints = [], []
    for ic in USADOS:
        m = re.search(r'\.ti-%s:before\{content:"\\([0-9a-fA-F]+)"\}' % re.escape(ic), texto)
        if not m:
            sys.exit(f'No se encontró el ícono ti-{ic}')
        cp = m.group(1).lower()
        codepoints.append(cp)
        reglas.append(f'.ti-{ic}:before{{content:"\\{cp}"}}')

    base_rule = (
        '.ti{font-family:"tabler-icons" !important;speak:none;font-style:normal;'
        'font-weight:normal;font-variant:normal;text-transform:none;line-height:1;'
        '-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}'
    )
    font_face = (
        '@font-face{font-family:"tabler-icons";font-style:normal;font-weight:400;'
        'src:url("./fonts/tabler-icons.subset.woff2") format("woff2")}'
    )
    salida = (
        '/* Tabler Icons — subset generado por scripts/subset_icons.py */\n'
        + font_face + '\n' + base_rule + '\n' + '\n'.join(reglas) + '\n'
    )
    (BASE / 'static' / 'css' / 'tabler-icons.subset.css').write_text(salida, encoding='utf-8')

    unicodes = ','.join(codepoints)
    print(f'CSS subset OK ({len(USADOS)} íconos).')

    # Subsetea la fuente automáticamente si fonttools está disponible.
    try:
        subprocess.run(
            [sys.executable, '-m', 'fontTools.subset', str(FONT_SRC),
             f'--unicodes={unicodes}', '--flavor=woff2',
             f'--output-file={FONT_OUT}'],
            check=True,
        )
        print(f'Fuente subset OK -> {FONT_OUT.name}')
    except (subprocess.CalledProcessError, FileNotFoundError):
        print('fonttools no disponible. Unicodes para pyftsubset:')
        print(unicodes)


if __name__ == '__main__':
    main()
