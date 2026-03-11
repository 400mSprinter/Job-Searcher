# Created: 2026-03-11 11:00
import anthropic
from resume import RESUME_TEXT


def match_job(job_posting: str) -> str:
    """Analyze job fit using Claude. Streams output to console and returns full text."""
    client = anthropic.Anthropic()

    prompt = f"""You are a career advisor analyzing job fit for a candidate applying for finance and business development roles.

CANDIDATE RESUME:
{RESUME_TEXT}

JOB POSTING:
{job_posting}

Analyze the fit between this candidate and the role. Structure your response exactly as follows:

## Fit Score
X/10 — [one-sentence rationale]

## Key Strengths
- [Specific match between candidate's experience and job requirement]
- [Continue for 3-5 bullet points]

## Gaps / Watch-outs
- [Missing requirement or potential concern]
- [Continue for 2-4 bullet points, or "None significant" if strong fit]

## Recommendation
[Apply confidently / Apply with tailored messaging / Skip — with 1-2 sentence reasoning]

## Application Tips
1. [Specific tip referencing actual details from the job posting]
2. [Another specific tip]
3. [Optional third tip if relevant]

Be direct and specific. Reference actual details from both the resume and job posting."""

    result = []
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            result.append(text)

    print()
    return "".join(result)
