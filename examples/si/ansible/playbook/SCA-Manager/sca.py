import sys
import yaml

def modify_rule(file_path, rule_numbers):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    if 'checks' not in data:
        print("Error: No se encontró la sección 'checks' en el archivo YAML.")
        return

    # Procesar solo la sección 'checks'
    for item in data['checks']:
        if isinstance(item, dict) and 'id' in item:
            try:
                item_id = int(item['id'])
                if item_id in rule_numbers:
                    item['title'] = "RULE DISABLED - " + item['title']
                    item['rules'] = ["d:/"]
            except ValueError:
                print(f"Advertencia: ID no numérico encontrado en el archivo: {item['id']}")

    with open(file_path, 'w') as file:
        yaml.dump(data, file)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <file_path> <rule_number1> <rule_number2> ...")
    else:
        file_path = sys.argv[1]
        rule_numbers = [int(num) for num in sys.argv[2:]]
        modify_rule(file_path, rule_numbers)

