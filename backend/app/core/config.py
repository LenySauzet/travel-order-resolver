from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pathlib import Path

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Travel Order Resolver API"
    app_description: str = "API for resolving travel orders"
    app_version: str = "0.1.0"
    debug: bool = False
    db_user: str = ""
    db_password: str = ""
    db_name: str = "test.db"
    navitia_api_key: str = ""
    navitia_base_url: str = "https://api.navitia.io/v1"
    navitia_coverage: str = "sncf"
    google_maps_api_key: str = ""

    @property
    def db_url(self):
        db_path = Path(__file__).parent.parent / "db" / self.db_name
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"


config = Config()