import json
import os
import random
import urllib.request
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from seeder.schema import TableSchema

load_dotenv()


class LLMRowGenerator:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

    def generate_rows_for_table(
        self,
        schema: TableSchema,
        count: int,
        available_parent_ids: Dict[str, Dict[str, List[Any]]],
    ) -> List[Dict[str, Any]]:
        """Generate `count` realistic rows for `schema.name` adhering to:
        1. FK Integrity (sampling from `available_parent_ids`)
        2. Schema-Agnostic Zero-Shot Cross-Column Logic (pure LLM semantic inference)
        """
        # Exclude autoincrement primary keys from LLM generation
        requested_cols = [c for c in schema.columns if not (c.is_pk and "INT" in c.type_name.upper())]

        col_descriptions = []
        for c in requested_cols:
            desc = f"{c.name} ({c.type_name})"
            if c.is_fk:
                desc += f" -> FK to {c.fk_target_table}.{c.fk_target_column}"
            col_descriptions.append(desc)

        # 100% SCHEMA-AGNOSTIC PROMPT: ZERO hardcoded table or column names!
        prompt = f"""You are an expert AI relational database seeder.
Generate exactly {count} realistic synthetic rows for the table '{schema.name}'.

Columns to populate:
{json.dumps(col_descriptions, indent=2)}

CRITICAL ZERO-SHOT CROSS-COLUMN COHESION INSTRUCTIONS:
- Analyze the semantic meaning of column names, data types, and implicit relationships in '{schema.name}'.
- Automatically identify any state/status columns and their associated conditional attributes (timestamps, resolution notes, cancellation reasons, escalation notes, failure codes, etc.).
- Maintain strict logical state-machine consistency within each row:
  * Active/Completed/Resolved/Shipped states MUST have valid timestamps, while cancellation/escalation/error notes MUST be null.
  * Cancelled/Failed/Escalated/Rejected states MUST have realistic explanation notes/reasons, while success timestamps MUST be null.
  * Pending/Open/Draft states MUST have null completion timestamps and null escalation/cancellation notes.
- Return ONLY a raw JSON array of {count} objects, where keys are exact column names: {[c.name for c in requested_cols]}.
- DO NOT wrap in markdown code blocks. Output raw JSON only.
"""

        rows = self._call_llm_json(prompt, count)

        final_rows = []
        for idx, row in enumerate(rows):
            processed_row = dict(row)

            # Enforce Foreign Keys from parent table generated IDs
            for c in schema.columns:
                if c.is_fk and c.fk_target_table:
                    target_table = c.fk_target_table
                    target_col = c.fk_target_column or "id"
                    if (
                        target_table in available_parent_ids
                        and target_col in available_parent_ids[target_table]
                        and available_parent_ids[target_table][target_col]
                    ):
                        possible_ids = available_parent_ids[target_table][target_col]
                        processed_row[c.name] = random.choice(possible_ids)

                elif c.is_pk and "INT" in c.type_name.upper():
                    if c.name in processed_row:
                        del processed_row[c.name]

            final_rows.append(processed_row)

        return final_rows

    def _call_llm_json(self, prompt: str, count: int) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(body).encode("utf-8"))
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```"):
                    lines = content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()
                return json.loads(content)
        except Exception as e:
            print(f"[Error] LLM API call failed: {e}")
            return []


def generate_sql_inserts(table_name: str, rows: List[Dict[str, Any]]) -> List[str]:
    """Convert a list of row dicts into valid SQL INSERT statements."""
    statements = []
    for row in rows:
        cols = list(row.keys())
        vals = []
        for c in cols:
            v = row[c]
            if v is None:
                vals.append("NULL")
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            elif isinstance(v, bool):
                vals.append("TRUE" if v else "FALSE")
            else:
                escaped = str(v).replace("'", "''")
                vals.append(f"'{escaped}'")

        col_str = ", ".join(cols)
        val_str = ", ".join(vals)
        statements.append(f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str});")

    return statements
