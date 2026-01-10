def get_offsets(full_text: str, substring: str, label: str) -> tuple[int, int, str]:
    start = full_text.find(substring)
    return (start, start + len(substring), label)
