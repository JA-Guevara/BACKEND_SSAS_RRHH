import re


def redact_personal_data(text: str, personal_values: list[str | None]) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"https?://\S+", "[URL]", text)

    def contact(match):
        value = match.group()
        if re.fullmatch(r"(?:19|20)\d{2}\s*-\s*(?:19|20)\d{2}", value):
            return value
        return "[CONTACTO]" if sum(c.isdigit() for c in value) >= 8 else value

    text = re.sub(r"(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)", contact, text)
    for value in sorted((v for v in personal_values if v and v.strip()), key=len, reverse=True):
        text = re.sub(
            r"(?<!\w)" + re.escape(value.strip()) + r"(?!\w)",
            "[OMITIDO]",
            text,
            flags=re.IGNORECASE,
        )
    text = re.sub(
        r"(?im)^\s*(?:CI|DNI|cedula|fecha de nacimiento|edad|genero|sexo|"
        r"estado civil|nacionalidad|direccion|telefono|celular)\s*[:=].*$",
        "[DATO PERSONAL]",
        text,
    )
    return text
