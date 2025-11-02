"""Text formatting utilities for enterprise-grade display"""
import re
from typing import Dict
from datetime import datetime

def format_llm_synthesis(raw_text: str, max_length: int = 200, truncate: bool = True) -> str:
    """
    Format raw LLM output into clean, professional text.

    Args:
        raw_text: Raw output from LLM agent
        max_length: Maximum character length for output (ignored if truncate=False)
        truncate: Whether to truncate text (set False for full detailed analysis)

    Returns:
        Formatted, clean text suitable for enterprise display
    """
    if not raw_text:
        return "Analysis in progress..."

    # Remove common LLM artifacts
    text = raw_text.strip()

    # Remove markdown formatting (headers, bold, italic, code)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Headers (# ## ### etc)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.+?)`', r'\1', text)        # Code
    text = re.sub(r'#+\s+', '', text)  # Any remaining headers (inline)

    # Remove multiple newlines
    text = re.sub(r'\n\s*\n', '. ', text)
    text = re.sub(r'\n', ' ', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    # PHASE 5 FIX: Only truncate if explicitly requested
    # Extract key sentence if text is too long
    if truncate and len(text) > max_length:
        # Try to find first complete sentence
        sentences = re.split(r'[.!?]\s+', text)
        if sentences and len(sentences[0]) < max_length:
            text = sentences[0].strip() + '.'
        else:
            # Truncate at word boundary
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    return text


def format_detailed_analysis(raw_analysis: str) -> str:
    """PHASE 5 FIX: Format detailed LLM analysis with proper structure and readability.

    Args:
        raw_analysis: Raw analysis text from LLM (long paragraph)

    Returns:
        Formatted analysis with sections, line breaks, and proper hierarchy
    """
    if not raw_analysis:
        return ""

    text = raw_analysis.strip()

    # Detect and format section headers (text followed by colon or dash markers)
    # Pattern: "Word Word Word:" or "- Section Header"
    lines = []

    # Split on common section markers but preserve them
    import re

    # Add line breaks before section headers (Capital letter + words + colon)
    # This pattern finds: "Word Word" followed by colon
    text = re.sub(r'([.!?])\s+([A-Z][a-zA-Z\s]+):', r'\1\n\n\2:', text)

    # Split into sentences but keep structure
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    current_section = None
    section_content = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if this is a section header (ends with colon)
        if sentence.endswith(':'):
            # Save previous section
            if current_section and section_content:
                lines.append(f"\n{current_section}")
                lines.extend(section_content)
                section_content = []
            elif not current_section and section_content:
                # PHASE 5 FIX: If we have content but no section header yet, save it as general content
                lines.extend(section_content)
                section_content = []

            current_section = sentence
            continue

        # Check if this is a numbered list item (1. 2. 3. etc)
        if re.match(r'^\d+\.\s', sentence):
            section_content.append(f"  {sentence}")
        # Check if this is a bullet point (- or *)
        elif re.match(r'^[-*]\s', sentence):
            section_content.append(f"  {sentence}")
        else:
            section_content.append(sentence)

    # Add last section
    if current_section and section_content:
        lines.append(f"\n{current_section}")
        lines.extend(section_content)
    elif not current_section and section_content:
        # PHASE 5 FIX: If we have content but no section header, return it directly
        lines.extend(section_content)

    return '\n'.join(lines)


def format_root_cause_analysis(root_cause: str, alerts_context: list = None) -> str:
    """
    Format root cause analysis for Why-Trace display.
    Clean format with uppercase headers, numbered lists, no emotes, no hardcoded numbers.

    Args:
        root_cause: Raw root cause text from orchestrator
        alerts_context: Optional list of alert details for context

    Returns:
        Well-formatted root cause analysis (plain text with clear structure)
    """
    if not root_cause or root_cause == "Processing...":
        return "Root cause analysis in progress. Agents are correlating alerts and metrics to determine the underlying issue."

    # Remove all emotes from the text
    emote_pattern = r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]'
    cleaned = re.sub(emote_pattern, '', root_cause)

    # Remove any remaining emoji-like characters
    cleaned = re.sub(r'[^\x00-\x7F\s]+', ' ', cleaned)

    # Remove ALL markdown formatting (bold, italic, headers, code)
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)  # Bold **text**
    cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned)      # Italic *text*
    cleaned = re.sub(r'__(.+?)__', r'\1', cleaned)      # Bold __text__
    cleaned = re.sub(r'_(.+?)_', r'\1', cleaned)        # Italic _text_
    cleaned = re.sub(r'`(.+?)`', r'\1', cleaned)        # Code `text`
    cleaned = re.sub(r'^#+\s+', '', cleaned, flags=re.MULTILINE)  # Headers

    # Clean up excessive whitespace but PRESERVE line breaks for structure
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Multiple spaces/tabs to single space
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Multiple blank lines to double newline
    cleaned = cleaned.strip()

    # If alerts_context provided, add PRIMARY ALERT section at the top
    if alerts_context and len(alerts_context) > 0:
        sections = []

        # Primary Alert Section
        primary_alert = alerts_context[0]
        alert_title = primary_alert.get('title', 'Unknown')
        host = primary_alert.get('host', 'Unknown')

        sections.append("PRIMARY ALERT")
        sections.append(f"{alert_title} on {host}")
        sections.append("")

        # Correlated Alerts Section (if multiple)
        if len(alerts_context) > 1:
            sections.append("CORRELATED ALERTS")
            sections.append(f"Total alerts: {len(alerts_context)}")
            for idx, alert in enumerate(alerts_context[1:], start=1):
                alert_title = alert.get('title', 'Unknown')
                alert_host = alert.get('host', 'Unknown')
                sections.append(f"{idx}. {alert_title} on {alert_host}")
            sections.append("")

        sections.append("ROOT CAUSE ANALYSIS")
        sections.append(cleaned)  # Add the full cleaned text WITHOUT re-numbering

        return "\n".join(sections)
    else:
        # No alerts context, just return cleaned analysis with header
        return f"ROOT CAUSE ANALYSIS\n{cleaned}"


def humanize_action_type(action_type: str) -> str:
    """
    Convert technical action types to human-readable format.

    Args:
        action_type: Technical action name (e.g., 'restart_service')

    Returns:
        Human-readable action name (e.g., 'Restarted Service')
    """
    # Define mappings for common action types
    mappings = {
        'suppress_alerts': 'Suppressed Alerts',
        'restart_service': 'Restarted Service',
        'deploy_patch': 'Deployed Patch',
        'clear_cache': 'Cleared Cache',
        'scale_resources': 'Scaled Resources',
        'rollback_patch': 'Rolled Back Patch',
        'deploy_canary': 'Deployed Canary',
        'verify_health': 'Verified Health',
        'run_preflight_checks': 'Ran Preflight Checks',
        'deploy_full_patch': 'Deployed Full Patch'
    }

    # Return mapped value or format the raw type
    if action_type in mappings:
        return mappings[action_type]

    # Fallback: capitalize and replace underscores
    return ' '.join(word.capitalize() for word in action_type.split('_'))


def humanize_status(status: str) -> str:
    """
    Convert technical status to human-readable format.

    Args:
        status: Technical status (e.g., 'in_progress')

    Returns:
        Human-readable status (e.g., 'In Progress')
    """
    return ' '.join(word.capitalize() for word in status.split('_'))


def format_incident_title(alert_title: str, severity: str = None) -> str:
    """
    Format incident title for display.

    Args:
        alert_title: Primary alert title
        severity: Optional severity level

    Returns:
        Formatted incident title
    """
    if not alert_title or alert_title == "System incident":
        return "System Incident Detected"

    # Ensure proper capitalization
    title = alert_title.strip()
    if title and not title[0].isupper():
        title = title[0].upper() + title[1:]

    return title


def format_timeline_event(agent_name: str, action: str = None) -> str:
    """
    Create descriptive timeline event text.

    Args:
        agent_name: Name of the agent
        action: Optional specific action taken

    Returns:
        Descriptive timeline event
    """
    descriptions = {
        'AlertOps': 'Analyzed and correlated related alerts',
        'PredictiveOps': 'Performed predictive analysis on metrics',
        'PatchOps': 'Evaluated patch requirements',
        'TaskOps': 'Automated remediation tasks',
        'Orchestrator': 'Synthesized findings and coordinated response'
    }

    if action:
        return f"{agent_name}: {action}"

    return descriptions.get(agent_name, f"{agent_name} processed incident data")


def truncate_smart(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Intelligently truncate text at word boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Try to truncate at sentence boundary
    truncated = text[:max_length]

    # Find last period, question mark, or exclamation
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct > max_length * 0.7:  # If we're not cutting too much
        return text[:last_punct + 1]

    # Otherwise truncate at word boundary
    return text[:max_length].rsplit(' ', 1)[0] + suffix


def format_datetime(dt_input, format_type: str = 'full') -> str:
    """
    Format datetime for enterprise display.

    Args:
        dt_input: datetime object or ISO string
        format_type: 'full', 'date', 'time', 'short'

    Returns:
        Formatted datetime string
    """
    # Convert to datetime object if string
    if isinstance(dt_input, str):
        try:
            dt = datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return dt_input  # Return as-is if can't parse
    elif isinstance(dt_input, datetime):
        dt = dt_input
    else:
        return str(dt_input)

    # Format based on type
    if format_type == 'full':
        # "Oct 17, 2025 at 7:04 PM"
        return dt.strftime('%b %d, %Y at %I:%M %p')
    elif format_type == 'date':
        # "Oct 17, 2025"
        return dt.strftime('%b %d, %Y')
    elif format_type == 'time':
        # "7:04 PM"
        return dt.strftime('%I:%M %p')
    elif format_type == 'short':
        # "Oct 17, 7:04 PM"
        return dt.strftime('%b %d, %I:%M %p')
    else:
        return dt.strftime('%b %d, %Y at %I:%M %p')
