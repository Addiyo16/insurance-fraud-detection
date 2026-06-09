import os
import re

POLICIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policies")

def retrieve_policy_context(domain, keywords=None):
    """
    RAG Retriever: Reads the markdown policy contract for a given domain and
    extracts the sections that match specific keywords or triggered fraud indicators.
    
    If no keywords match, it returns the standard 'Exclusions' and 'Coverage' sections.
    """
    filename = f"{domain.lower()}_policy.md"
    file_path = os.path.join(POLICIES_DIR, filename)

    if not os.path.exists(file_path):
        print(f"Policy file not found: {file_path}")
        return "No standard policy contract found for this domain."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split content into headers / sections
        # Match markdown headers: e.g., '## Section Name' or '# Main Header'
        sections = re.split(r'\n(?=#{1,3}\s)', content)
        
        matched_sections = []
        
        # Prepare keyword search list
        search_terms = ["exclusion", "limit", "verify", "audit"]
        if keywords:
            if isinstance(keywords, list):
                search_terms.extend([k.lower() for k in keywords])
            else:
                search_terms.append(keywords.lower())

        # Scan and filter sections
        for section in sections:
            section_lower = section.lower()
            if any(term in section_lower for term in search_terms):
                matched_sections.append(section.strip())

        # If nothing matched, return the entire contract as fallback
        if not matched_sections:
            return content.strip()

        return "\n\n".join(matched_sections)

    except Exception as e:
        print(f"RAG Retrieval Error for {domain}: {e}")
        return "Error retrieving policy clauses."
