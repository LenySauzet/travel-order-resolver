"""
Point d'entrée principal du projet Travel Order Resolver.

Pour lancer l'API FastAPI:
    uv run uvicorn api.main:app --reload

Pour lancer le frontend Streamlit:
    uv run streamlit run frontend/app.py
"""


def main():
    print("Travel Order Resolver")
    print("=" * 40)
    print()
    print("Pour lancer l'API FastAPI:")
    print("  uv run uvicorn api.main:app --reload")
    print()
    print("Pour lancer le frontend Streamlit:")
    print("  uv run streamlit run frontend/app.py")


if __name__ == "__main__":
    main()
