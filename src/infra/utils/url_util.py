

def parse_url(path: str, params: dict) -> str:
    queries = []
    for key, value in params.items():
        queries.append(f'{key}={value}')
    
    return f'''{path}{'&'.join(queries)}'''
