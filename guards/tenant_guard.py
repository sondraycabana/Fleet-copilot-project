from typing import Dict, Any

class TenantGuard:
    @staticmethod
    def validate_query_isolation(sql_query: str, authorized_company_id: str) -> str:
        cleaned_query = sql_query.lower()
        if "snapshots" in cleaned_query:
            expected_clause = f"company_id = '{authorized_company_id.lower()}'"
            expected_clause_alt = f"company_id='{authorized_company_id.lower()}'"
            if (expected_clause not in cleaned_query) and (expected_clause_alt not in cleaned_query):
                raise PermissionError(f"Security Exception: Query lacks company isolation for '{authorized_company_id}'.")
        return sql_query
