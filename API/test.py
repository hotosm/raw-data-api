import re


def replace_key(input_str):
    pattern = r"tags\['([^']+)'\]\[1\]"
    match = re.search(pattern, input_str)

    if match:
        key = match.group(1)
        return input_str.replace(match.group(0), key)
    else:
        return input_str


# Example usage:
input_str = "tags['railway'][1] IN ('rail','station')"
result = replace_key(input_str)

print(result)
