p1 = {
    'limit': 10,
    'type': 'active',
    'offset': 0,
}

p2 = {
    'order[timestamp]': 'DESC',
    'order[price]': 'ASC',
    'order[side]': 'ASC',
    'order[type]': 'ASC',
    'order[executed]': 'ASC',
    'order[executedPrice]': 'ASC'
}

p3 = {
    'timestamp': 'DESC',
    'price': 'ASC',
    'side': 'ASC',
    'type': 'ASC',
    'executed': 'ASC',
    'executedPrice': 'ASC'
}

p4 = {
    'timestamp': 'DESC',
    'pric': 'ASC',
    'side': 'ASC',
    'type': 'ASC',
    'executed': 'ASC',
    'executedPrice': 'ASC'
}

order_by = {
    'order[timestamp]': 'DESC',
    'order[price]': 'ASC',
    'order[side]': 'ASC',
    'order[type]': 'ASC',
    'order[executed]': 'ASC',
    'order[executedPrice]': 'ASC'
}

def form_order_by(order: dict) -> dict:
    valid_keys = ('timestamp', 'price', 'side', 'type', 'executed', 'executedPrice')
    formatted_order = {}
    for key, value in order.items():
        if key in valid_keys:
            f_key = f"order[{key}]"
            formatted_order[f_key] = value
        else:
            print(f"Не корректная Попытка указать порядок вывода Ордеров. | Ключ '{key}' НЕ Актуален")
    return formatted_order

if __name__ == '__main__':
    p = p1 | p2
    print(f"{p = }")
    print(f"{form_order_by(p3) = }")
    print(f"{form_order_by(p4) = }")
    print(f"{len(p) = }")
    p1 = p1 | p2
    print(f"{p1 = }")



