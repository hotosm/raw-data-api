from transliterate import translit, get_available_language_codes


class Transliterator:
    """Used for transliterate names while processing GeoJSON files line by line"""

    props = "properties"

    def __init__(self):
        self.available_language_codes = get_available_language_codes()
        self.name_tags = [f"name:{x}" for x in self.available_language_codes]

    def translit(self, line):
        """
        Transliterate names and add a new tag suffixed with -translit
        """
        for code in self.available_language_codes:
            tag = "name:{code}".format(code=code)
            prop = (
                line["properties"]["tags"]
                if self.props == "properties.tags"
                else line["properties"]
            )
            if tag in prop:
                translit_tag = "{tag}-translit".format(tag=tag)
                if not translit_tag in prop:
                    if self.props == "properties.tags":
                        line["properties"]["tags"][translit_tag] = translit(
                            prop[tag], code, reversed=True
                        )
                    else:
                        line["properties"][translit_tag] = translit(
                            prop[tag], code, reversed=True
                        )
