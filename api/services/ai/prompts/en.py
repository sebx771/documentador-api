# English prompt configurations

EN_STRUCTURE_CHUNK = """
### [Module/File Name]
- **Description**: Brief technical summary (1-2 sentences).
- **Components**: Key classes, functions, or structures.
- **Logic & Validations**: Essential flow and implementation details.
"""

EN_STRUCTURE_FINAL = """
# [Project or System Title]

## 1. Executive Summary
Purpose, users, and main capabilities based strictly on the available sources.

## 2. Component Architecture
Describe the frontend, backend, persistence, and integrations and how they relate. Include a concise table of key components.

## 3. Core Logic & Business Rules
Explain end-to-end business flows connecting routes, middleware, controllers, and services.

## 4. Data Model
Summarize entities, relationships, and constraints present in models or schema.

## 5. API & Permissions
Document method, route, purpose, and verified authentication/authorization for each endpoint.

## 6. Setup & Execution (Conditional)
Include requirements, commands, and environment variables only when present in the sources. Identify conflicts between instructions and code.

## 7. Per-File Reference (Optional)
Include only important details not already explained above; avoid repeating a summary for every file.
"""

EN_CONSOLIDATION_PROMPT = """
Act as a software architect and senior technical editor. Turn the chunk analyses into one coherent system guide; do not return a collection of per-file summaries.

GOLDEN RULES:
1. **Factuality**: Use only facts in the supplied documentation; do not invent routes, contracts, variables, HTTP statuses, or behavior.
2. **Synthesis**: Deduplicate concepts and explain relationships and flows between components. Do not create one heading per file.
3. **Priority**: Summarize purpose, architecture, business rules, data model, and API/permissions first. Retain per-file details only when they add information not covered by the synthesis.
4. **Traceability**: Include source paths beside relevant technical claims when available.
5. **Uncertainty**: Explicitly identify contradictions or missing information instead of guessing.
6. **Format**: Follow the target structure included in the user message. Omit conditional sections when unsupported. Respond only in English.

"""

EN_CONFIGS = {
    "markdown": {
        "role": "Senior Software Engineer",
        "objective": "Technical analysis of a code module for integration into a larger report",
        "format_instructions": """
- Use Markdown with ## and ### headings
- Wrap variables and functions in `inline code` (IMPORTANT)
- Keep analysis concise, factual, and strictly accurate to the code
- Avoid fluff or robotic introductory phrases.
""",
        "structure": EN_STRUCTURE_FINAL,
    }
}

EN_REFERENCE_TEMPLATE = """
### [X]. Component Analysis (Reference Example)
| Module/Class | Responsibility | Key Functions/Logic |
| :--- | :--- | :--- |
| [Name] | [Primary function of the component] | [Key method or logic flow] |
"""

EN_CHUNK_PROMPT = """
ACTIVE CHUNK MODE:
1. FORBIDDEN: Do not generate level 1 headings (#), introductions, or table of contents.
2. FOCUS: Generate a brief technical analysis following EN_STRUCTURE_CHUNK.
3. FACTUAL: Do not guess logic outside this chunk. Write concisely to facilitate consolidation.
"""
