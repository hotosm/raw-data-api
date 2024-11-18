from transliterate import translit, get_available_language_codes


class Transliterator:
    """Used for transliterate names while processing GeoJSON files line by line"""

    def __init__(self):
        self.available_language_codes = get_available_language_codes()
        self.name_tags = [f"name:{x}" for x in self.available_language_codes]

    def translit(self, line):
        """
        Transliterate names and add a new tag suffixed with -translit
        """
        for code in self.available_language_codes:
            tag = "name:{code}".format(code=code)
            if tag in line["properties"]["tags"]:
                translit_tag = "{tag}-translit".format(tag=tag)
                if not translit_tag in line["properties"]["tags"]:
                    line["properties"]["tags"][translit_tag] = translit(
                        line["properties"]["tags"][tag], code, reversed=True
                    )
