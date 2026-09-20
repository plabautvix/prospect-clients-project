# backend

FastAPI + SQLAlchemy. Camadas: Controller -> Service -> Repository.

Visão geral da arquitetura e análise de segurança: [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

## Migrations

O schema pertence ao Alembic. A aplicação **não** cria nem altera tabela: o
`alembic upgrade head` roda como passo separado antes do uvicorn (ver
`Dockerfile`).

`migrations/env.py` lê a URL de `configurations/database.py`, então a string de
conexão tem uma só fonte de verdade e o `alembic.ini` só carrega um placeholder.

```bash
alembic upgrade head          # aplica o que falta
alembic current               # em que revisão o banco está
alembic history               # lista as revisões
alembic downgrade -1          # volta uma
```

Para criar uma nova:

```bash
alembic revision --autogenerate -m "descricao curta"
```

Revise o arquivo gerado antes de aplicar. O `render_as_batch=True` está ligado
porque o SQLite não faz `ALTER` na maioria dos casos: o batch mode recria a
tabela. É inofensivo em outros bancos.

### Banco que existia antes do Alembic

Um `test.db` criado pelo antigo `Base.metadata.create_all` já tem as tabelas,
então rodar `upgrade head` nele falha com `table user already exists`. Marque a
revisão sem executá-la:

```bash
alembic stamp head
```

Isso só grava a versão na tabela `alembic_version`, sem tocar em dado nenhum.

## Testes

```bash
pytest
```

Os testes usam SQLite em memória com `create_all` (`tests/conftest.py`), não o
Alembic: cada teste quer um schema novo e vazio, não o histórico de migrations.
