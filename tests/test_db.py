from sqlalchemy import Engine, text


def test_engine_connects_to_test_database(engine: Engine) -> None:
    with engine.connect() as conn:
        assert conn.execute(text("SELECT current_database()")).scalar() == "copilot_test"
