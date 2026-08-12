class TextHepler:
    @staticmethod
    def split_text(text) -> list:
        return text.replace("  ", "").split(",")

    @staticmethod
    def take_inn(text: list) -> int:
        return int([i for i in text if "ИНН" in i][0].split(":")[-1].strip())

    @staticmethod
    def take_name(text: list) -> str:
        return text[0] 