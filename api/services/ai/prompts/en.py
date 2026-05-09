# English prompt configurations

EN_STRUCTURE_CHUNK = """
### [Module/File Name]
- **Description**: Brief technical summary.
- **Components**: List of key classes or functions (use tables only if very complex).
- **Logic & Validations**: Key implementation points.
- **Errors**: Summary of exceptions or error codes detected.
"""

EN_STRUCTURE_FINAL = """
# [Project or System Title]

## 1. Executive Summary (Overview)
Brief description of the overall purpose of the system.

## 2. Component Architecture
Consolidated table of all modules, their responsibilities, and key functions.

## 3. Core Logic and Business Rules
Detailed explanation of main flows and validations.

## 4. Error & Exception Matrix
Consolidated table of error codes, HTTP statuses, and conditions.

## 5. Integration / Usage Guide
Examples of endpoints, parameters, and necessary configuration.
"""

EN_CONSOLIDATION_PROMPT = """
Act as a Senior Technical Editor. Your task is to CONSOLIDATE multiple documentation fragments into a single, professional, and coherent document.

GOLDEN RULES:
1. **Deduplication**: If multiple fragments mention the same component or error, merge them into a single entry.
2. **Master Tables**: Merge all "Components and Services" tables into a SINGLE master table in the Architecture section.
3. **Error Matrix**: Merge all error codes into a SINGLE coherent table.
4. **Flow**: Write transitions between sections so it doesn't look like a list of pasted fragments.
5. **Format**: Strictly follow the level 1 (#) and level 2 (##) structure defined in STRUCTURE_FINAL.
6. **Language**: Respond ONLY in English.

DOCUMENT TO CONSOLIDATE:
"""

EN_CONFIGS = {
    "markdown": {
        "role": "Senior Software Engineer",
        "objective": "Technical analysis of a code module for integration into a larger report",
        "format_instructions": """
- Use Markdown with ## and ### headings
- Wrap variables and functions in `inline code` (IMPORTANT)
- Adapt the level of detail according to code complexity
- Use technical but natural language, avoiding sounding robotic.
""",
        "structure": EN_STRUCTURE_FINAL,  # Default
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
2. FOCUS: Generate the technical analysis following the CHUNK_STRUCTURE.
3. CONTINUITY: Write so it is easy to consolidate later.
"""
