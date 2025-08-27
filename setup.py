# setup.py
from cx_Freeze import setup, Executable
from pathlib import Path

include_files = [
    ("finance.db", "finance.db"),
    ("assets", "assets"),
]

build_exe_options = {
    # Pacotes que seu app usa de verdade
    "packages": [
        # Dash + Flask
        "dash", "dash_bootstrap_components", "dash_iconify",
        "flask", "flask_compress", "jinja2", "werkzeug", "itsdangerous", "click",
        # Data / cálculo
        "pandas", "numpy", "dateutil", "pytz", "tzdata",
        # Gráficos
        "plotly", "packaging", "tenacity",
        # Rede
        "requests", "urllib3", "certifi", "idna", "charset_normalizer",
        # Seu código
        "services", "components",
        # Sync de cotações
        "yfinance",
    ],
    # EXCLUIR coisas opcionais que aparecem como "missing" mas você não usa
    "excludes": [
        "IPython", "pytest", "dash.testing", "matplotlib", "scipy", "skimage",
        "pyspark", "dask", "duckdb", "polars", "cupy", "cudf", "pyarrow",
        "celery", "diskcache", "bs4", "selenium", "anywidget", "orjson",
        "OpenSSL", "cryptography", "PIL", "brotli", "brotlicffi",
    ],
    "include_files": include_files,
    "include_msvcr": True,
}

BASE = "Win32GUI"  # troque para None se quiser console p/ debug

setup(
    name="ControleFinanceiro",
    version="0.1.0",
    description="Aplicação Controle Financeiro (Dash)",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "myindex.py",
            target_name="ControleFinanceiro",
            base=BASE,
            icon=str(Path("assets/pantera.ico")) if Path("assets/pantera.ico").exists() else None,
        )
    ],
)
