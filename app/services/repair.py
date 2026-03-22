def extract_first_json_object(raw_output: str) -> str:
    start_index = raw_output.find("{")
    if start_index == -1:
        raise ValueError("No JSON object found.")

    depth = 0
    for index in range(start_index, len(raw_output)):
        char = raw_output[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw_output[start_index : index + 1]

    raise ValueError("Unterminated JSON object.")
