
def parse_float(text):
    """cos it blows up on None"""
    if text:
        return float(text)
    return 0
