# Começando

## Requisitos

- Python 3.12+
- pip
- Ambiente virtual recomendado

## Instalação Local (Windows PowerShell)

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

## Rodar Testes

```powershell
# Rodar todos os testes
pytest -v

# Rodar testes de um módulo específico
pytest tests/test_normalizer.py -v
pytest tests/test_comparator.py -v
pytest tests/test_insight_generator.py -v
pytest tests/test_pipeline.py -v
pytest tests/test_analyze_lap_script.py -v
pytest tests/test_analyze_lap_with_reference_script.py -v
```

## Nota sobre Testes

É possível que 1 teste apareça como `skipped` quando CSVs reais não estiverem presentes na pasta `data/`. Isso é normal e não indica um problema com o código.
