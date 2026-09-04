from collections import defaultdict, deque
from typing import Dict, List
from seeder.schema import TableSchema


def topological_sort_tables(schemas: Dict[str, TableSchema]) -> List[str]:
    """Sort tables topologically so parent tables come before child tables.
    
    If table B has a Foreign Key pointing to table A, then A is a parent of B,
    so A MUST appear before B in the returned list.
    """
    in_degree: Dict[str, int] = {t: 0 for t in schemas}
    graph: Dict[str, List[str]] = defaultdict(list)

    for table_name, schema in schemas.items():
        for parent in schema.parent_tables:
            if parent in schemas and parent != table_name:
                graph[parent].append(table_name)
                in_degree[table_name] += 1

    queue = deque([table for table, degree in in_degree.items() if degree == 0])
    sorted_order = []

    while queue:
        node = queue.popleft()
        sorted_order.append(node)

        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_order) < len(schemas):
        # Handle cycles gracefully by appending remaining tables
        remaining = [t for t in schemas if t not in sorted_order]
        sorted_order.extend(remaining)

    return sorted_order
