from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_NEWS_RSS_URLS = (
    "https://news.google.com/rss/search?q=Borsa+Istanbul&hl=tr&gl=TR&ceid=TR:tr,"
    "https://news.google.com/rss/search?q=BIST+hisse&hl=tr&gl=TR&ceid=TR:tr,"
    "https://news.google.com/rss/search?q=KAP+borsa&hl=tr&gl=TR&ceid=TR:tr"
)


class Settings(BaseSettings):
    app_name: str = "BIST Katılım AI Predictor"
    app_version: str = "0.1.0"
    environment: str = "development"

    supabase_url: str = ""
    supabase_key: str = ""
    self_test_token: str = ""

    # Override with NEWS_RSS_URLS. Use KAP_RSS_URLS only for an authorized
    # KAP distributor/feed; KAP's official data API requires a data contract.
    news_rss_urls: str = DEFAULT_NEWS_RSS_URLS
    kap_rss_urls: str = ""
    news_fetch_timeout_seconds: int = 10
    # Optional comma-separated SYMBOL:SECTOR pairs, e.g. AAA:ENERGY,BBB:BANK
    sector_map: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
