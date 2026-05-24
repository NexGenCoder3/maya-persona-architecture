from engine.session import PersonaSession


def main() -> None:
    session = PersonaSession.create_default()
    session.loop()


if __name__ == "__main__":
    main()
