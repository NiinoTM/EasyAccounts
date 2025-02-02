import unicodedata

def select_from_list(items, prompt, key='name', min_confidence=0.6):
    """
    Interativamente pesquisa e seleciona um item de uma lista.
    Permite busca por nome ou ID, com suporte a caracteres especiais.
    
    Args:
        items (list): A list of objects to select from.
        prompt (str): The prompt message to display.
        key (str): The attribute name to use for searching and displaying.
    
    Returns:
        The selected item from the list or None if canceled.
    """
    current_matches = items.copy()
    
    while True:
        # Mostra os itens encontrados
        if current_matches:
            print("\nItens encontrados:")
            for i, item in enumerate(current_matches, 1):
                attribute = getattr(item, key, '')
                print(f"{i}. {attribute} (ID: {item.id})")
            
            # Seleção automática se houver apenas um item
            if len(current_matches) == 1:
                attribute = getattr(current_matches[0], key, '')
                print(f"\nItem único encontrado: {attribute}")
                return current_matches[0]
        else:
            print("\nNenhum item encontrado. Tente novamente.")
            current_matches = items.copy()
        
        # Obtém a entrada do usuário
        user_input = input(f"\n{prompt} (digite o número, novo termo, ou 'sair'): ").strip().lower()
        
        # Verifica se o usuário digitou um número
        if user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(current_matches):
                return current_matches[index]
            print("Número inválido. Tente novamente.")
            continue
        
        # Verifica se o usuário digitou 'sair'
        if user_input == 'sair':
            return None
        
        # Filtra os itens com base no termo de busca
        if user_input:
            # Normaliza a entrada e os nomes dos itens para lidar com caracteres especiais
            normalized_input = unicodedata.normalize('NFD', user_input)\
                .encode('ascii', 'ignore').decode('ascii').lower()
            
            current_matches = [
                item for item in current_matches
                if (normalized_input in unicodedata.normalize('NFD', getattr(item, key, ''))
                    .encode('ascii', 'ignore').decode('ascii').lower()) or
                (user_input.isdigit() and item.id == int(user_input))
            ]
        else:
            print("Entrada inválida. Tente novamente.")
