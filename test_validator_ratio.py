#!/usr/bin/env python3
"""Test the validator frequency logic with different builder/validator ratios."""
import re

def check_ratio(content, label):
    builder_count = len(re.findall(r'^-\s+\*\*Role\*\*:\s*builder\s*$', content, re.MULTILINE))
    validator_count = len(re.findall(r'^-\s+\*\*Role\*\*:\s*validator\s*$', content, re.MULTILINE))
    if builder_count > 5:
        required = (builder_count // 5) + 1
        ok = validator_count >= required
    else:
        required = 1
        ok = validator_count >= 1
    status = 'PASS' if ok else 'BLOCK'
    print(f'{label}: {builder_count}B/{validator_count}V, need>={required}V -> {status}')

SECTIONS = '\n'.join([
    '## Task Description', '## Objective', '## Relevant Files',
    '## Step by Step Tasks', '## Acceptance Criteria',
    '## Team Orchestration', '### Team Members',
])

def make(b, v):
    roles = '\n'.join(['- **Role**: builder'] * b + ['- **Role**: validator'] * v)
    return SECTIONS + '\n' + roles

# Actual plan
with open('specs/metric-history-endpoint.md') as f:
    check_ratio(f.read(), 'Actual plan (5B/1V)')

check_ratio(make(6, 1), '6B/1V')
check_ratio(make(6, 2), '6B/2V')
check_ratio(make(12, 2), '12B/2V')
check_ratio(make(12, 3), '12B/3V')
check_ratio(make(3, 1), '3B/1V')
check_ratio(make(11, 3), '11B/3V')
check_ratio(make(11, 2), '11B/2V')
