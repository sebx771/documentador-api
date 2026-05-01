# English prompt configurations

EN_CONFIGS = {
    "markdown": {
        "role": "Senior Software Engineer",
        "objective": "Technical analysis of a code module for integration into a larger report",
        "format_instructions": """
- Use Markdown with ## and ### headings
- Wrap variables and functions in `inline code` (IMPORTANT)
- **COMPONENTS AND SERVICES:** ALWAYS list them in a table with columns: [Name, Responsibility, Key Logic/Functions].
- **ERROR CODES:** ALWAYS list them in a table with columns: [Status/Code, Constant, Condition/Reason].
- Use bulleted lists for business rules
- Adapt the level of detail according to code complexity
- Omit tables if there are no fields to document
- Use technical but natural language, avoiding sounding robotic or excessively formal.
""",
        "structure": """
### Suggested Structure:
1. # Title: Module or System Name
2. ## 1. Overview / Definition
3. ## 2. Component Architecture (Use Tables)
4. ## 3. Core Logic & Validations
5. ## 4. Error & Exception Handling (Use Tables)
6. ## 5. Integration / Usage Guide
"""
    }

}

EN_REFERENCE_TEMPLATE = """
### [X]. Component Analysis (Reference Example)
| Module/Class | Responsibility | Key Functions/Logic |
| :--- | :--- | :--- |
| [Name] | [Primary function of the component] | [Key method or logic flow] |

### [X]. API & Error Matrix (Reference Example)
| Status | Error Constant | Reason/Condition |
| :--- | :--- | :--- |
| [400/500] | [ERROR_CODE_NAME] | [Description of what triggers this error] |
"""

EN_CHUNK_PROMPT = """
ACTIVE CHUNK MODE:
1. FORBIDDEN: Do not generate level 1 headings (#), introductions, scopes, or table of contents.
2. FOCUS: Start directly with the technical analysis of the provided files.
3. HIERARCHY: Use level ### headings for each component or file analyzed.
4. CONTINUITY: Write the content as if it were an intermediate chapter of a technical book.
5. SYNTHESIS: If there is repeated logic among files in the same chunk, group them into a single explanation.
"""
