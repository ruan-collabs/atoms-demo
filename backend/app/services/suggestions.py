"""Structured next-step metadata; never execute suggestions or make model calls here."""
import json
import re
import unicodedata


def normalize(text):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', text).casefold())


def clean_suggestions(value, *, key='', current_prompt=''):
    if not isinstance(value, list) or len(value) != 2:
        return []
    result=[]
    seen=set()
    for item in value:
        if not isinstance(item, dict):return []
        label=item.get('label');prompt=item.get('prompt')
        if not isinstance(label,str) or not isinstance(prompt,str):return []
        label=label.strip();prompt=prompt.strip()
        if not (1 <= len(label) <= 24 and 1 <= len(prompt) <= 400):return []
        combined=label+' '+prompt
        if any(ord(c)<32 for c in combined) or re.search(r'<|>|https?://|(?<![\w-])sk-|Bearer\s+',combined,re.I):return []
        if key and key in combined:return []
        normalized=normalize(prompt)
        if not normalized or normalized in seen or normalized==normalize(current_prompt):return []
        if normalize(label) in seen or normalize(label)==normalize(current_prompt):return []
        seen.add(normalized);seen.add(normalize(label))
        result.append({'label':label,'prompt':prompt})
    return result


def suggestions_from_plan(plan, *, key='', current_prompt=''):
    try:
        raw=plan.strip()
        if raw.startswith('```'):
            raw=re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        data=json.loads(raw)
        return clean_suggestions(data.get('suggestions'),key=key,current_prompt=current_prompt) if isinstance(data,dict) else []
    except (ValueError,TypeError):return []
