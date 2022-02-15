class OptaUpgrade:
    successful = False

    @classmethod
    def success(cls) -> None:
        cls.successful = True

    @classmethod
    def unset(cls) -> None:
        cls.successful = False
