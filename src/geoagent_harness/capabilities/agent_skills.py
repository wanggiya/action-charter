"""Reviewed, non-executable agent know-how; never an operation or authority source."""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from pydantic import BaseModel, ConfigDict, Field, model_validator
from geoagent_harness.contracts.model_providers import DataClass

MAX_FILE_BYTES = 4096
MAX_CONTEXT_BYTES = 2600
MAX_SELECTED = 3
# Content pinning is part of source review. Project-local files cannot enroll themselves.
REVIEWED = {'csv-to-postgres': 'e1072e526b6274f718d9636e94ed801d73d5f313be544454b547a53ee5da27eb',
 'health-table-analysis': 'bbeab0ba946c90db1bafa5ebe68f881f16efbbd6e79a22efbb51649533edb4b0',
 'plain-language-report': 'e1dd4ad087be1606208bc1850c7106be0e8d9c6c1040dd9f3fdb57735d440270',
 'refuse-clearly': 'c8176ccef61b4861601b376cb399b40192bdd43cb3eb268e4f3f22d433250951',
 'table-analysis': '37c2c249411da1df036105c2d292d721e6e7bc8b696d3b7f90d8445fcf58ab9f',
 'vector-to-postgis': 'fd0bdc966dec0f309126ba17a1d59bcd3c10a9188a1dca80b748e2950c6d305a'}


class Header(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    id: str = Field(pattern=r'^[a-z][a-z0-9-]{0,63}$')
    version: str = Field(pattern=r'^\d+\.\d+\.\d+$', max_length=30)
    description: str = Field(min_length=1, max_length=180)
    when_to_use: list[str] = Field(min_length=1, max_length=16)
    operations: list[str] = Field(max_length=12)
    data_classes: list[DataClass] = Field(min_length=1, max_length=5)
    family: str | None = Field(default=None, pattern=r'^[a-z][a-z0-9-]{0,63}$')
    specificity: int = Field(default=0, ge=0, le=3, strict=True)

    @model_validator(mode='after')
    def bounded(self):
        if '\n' in self.description or '\r' in self.description or (self.specificity and not self.family):
            raise ValueError('Description must be one line; specificity needs a family')
        if any(not term.strip() or len(term)>64 or '\n' in term for term in self.when_to_use):
            raise ValueError('Invalid applicability keyword')
        if any(not re.fullmatch('[a-z][a-z0-9_]{0,79}', value) for value in self.operations):
            raise ValueError('Invalid operation ID')
        for values in (self.when_to_use, self.operations, self.data_classes):
            if len(set(values)) != len(values):
                raise ValueError('Duplicate header entries')
        return self


def _builtin_root():
    packaged = Path(__file__).parent / '_agent_skills'
    return packaged if packaged.is_dir() else Path(__file__).parents[3] / 'agent-skills'


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _read(root, skill_id, expected_sha256, known_operations):
    with ExitStack() as stack:
        directory = os.open(root, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        folder = os.open(skill_id, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=directory)
        stack.callback(os.close, folder)
        fd = os.open('SKILL.md', os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK, dir_fd=folder)
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            raise ValueError('Instruction file is not bounded regular content')
        content = os.read(fd, MAX_FILE_BYTES+1)
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError('Instruction content is not reviewed')
    text = content.decode('utf-8')
    if not text.startswith('---\n'):
        raise ValueError('A JSON front matter header is required')
    metadata, body = text[4:].split('\n---\n', 1)
    header = Header.model_validate(json.loads(metadata, object_pairs_hook=_pairs))
    if header.id != skill_id or not set(header.operations).issubset(known_operations) or not body.strip():
        raise ValueError('Header does not match registered capabilities')
    return header, body.strip()


def select(message, *, available, known_operations, focused_operations, cards=(), budget=MAX_CONTEXT_BYTES):
    """Selection is advisory. Never change available operations or egress permission."""
    if type(budget) is not int or not 0 <= budget <= MAX_CONTEXT_BYTES:
        raise ValueError('Invalid agent instruction budget')
    text = message[:8000].casefold()
    field_text = ' '.join(field['name'] for card in cards for field in card.get('fields',[])).casefold()[:4000]
    classes = {'metadata', 'data_card'} if cards else {'metadata'}
    eligible, omitted = [], []
    scope = set(available).intersection(focused_operations)
    for skill_id, sha in REVIEWED.items():
        try:
            header, body = _read(_builtin_root(), skill_id, sha, set(known_operations))
        except (ValueError, OSError, UnicodeError, RecursionError):
            omitted.append({'id':skill_id,'reason':'unavailable_or_unreviewed'})
            continue
        if not set(header.operations).issubset(scope) or not classes.intersection(header.data_classes):
            continue
        matches = [term for term in header.when_to_use if re.search(r'(?<!\w)'+re.escape(term.casefold())+r'(?!\w)', text)]
        fields = [term for term in header.when_to_use if re.search(r'(?<!\w)'+re.escape(term.casefold())+r'(?!\w)',field_text)]
        if matches or fields:
            eligible.append((len(matches)*2+bool(fields), header, body, sha, 'request_and_card' if fields else 'request'))
    specific = {}
    for _, header, *_ in eligible:
        if header.family:
            specific[header.family]=max(specific.get(header.family,0),header.specificity)
    retained=[]
    for entry in eligible:
        header=entry[1]
        if header.family and header.specificity<specific[header.family]:
            omitted.append({'id':header.id,'reason':'more_specific_method'})
        else:retained.append(entry)
    eligible=retained
    eligible.sort(key=lambda item:(-item[0], item[1].id))
    items, selected = [], []
    for _, header, body, sha, basis in eligible:
        item = {'id':header.id,'version':header.version,'guidance':body}
        candidate = items+[item]
        if len(items)>=MAX_SELECTED or len(json.dumps(candidate,separators=(',',':')).encode())>budget:
            omitted.append({'id':header.id,'reason':'context_budget'})
            continue
        items.append(item)
        selected.append({'id':header.id,'version':header.version,'sha256':sha,'basis':basis})
    receipt = {'version':'agent-knowhow-v1','status':'included' if items else 'none',
               'selected':selected,'omitted':omitted,'bytes':len(json.dumps(items,separators=(',',':')).encode()) if items else 0,
               'authority_granted':False}
    return items, receipt
