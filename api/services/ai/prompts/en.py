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
    },
    "pdf": {
        "role": "Senior Software Engineer",
        "objective": "Formal Technical Report for PDF export",
        "format_instructions": """
- DO NOT use Markdown tables (e.g., |---|). Use hyphenated lists to describe variables.
- DO NOT use bold with asterisks (e.g., **text**). Write clean text.
- For section headings, use ONLY the '## ' prefix followed by the name.
- Code blocks must be between triple backticks ``` only at the start and end.
- DO NOT use special characters like emojis or complex symbols outside of Latin-1.
- Explain logic step-by-step professionally.
""",
        "structure": """
### Required Sections:
1. Introduction and Code Scope
2. Data Dictionary (Fields, types, and purposes)
3. Business Logic and Use Cases
4. Technical Conclusions for the Report
"""
    },
    "word": {
        "role": "Software Development Analyst",
        "objective": "Technical Requirements Document in Microsoft Word",
        "format_instructions": """
- Generate detailed and extensive descriptions
- Structure with clear Word section headings
- Include a Technical Glossary if there are complex terms
- Write business rules as functional requirements
""",
        "structure": """
### Required Sections:
1. Introduction and Code Scope
2. Data Dictionary (Fields, types, and purposes)
3. Business Logic and Use Cases
4. Technical Conclusions for the Report
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
