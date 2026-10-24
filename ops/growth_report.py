#!/usr/bin/env python3
"""Offline cohort report from reconciled exports. No network or database writes."""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def timestamp(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamps must include a timezone')
    return parsed.astimezone(timezone.utc)


def ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'percent': round(100 * numerator / denominator, 2) if denominator else None}


def unique(rows, key):
    values = [r[key] for r in rows]
    if any(not isinstance(v, str) or not v for v in values) or len(set(values)) != len(values):
        raise ValueError(f'Missing/duplicate {key}')


def analyze(data):
    """All null milestones mean confirmed absent, never missing export coverage."""
    if data.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    as_of = timestamp(data['as_of'])
    if not as_of:
        raise ValueError('as_of is required')
    required = ('accounts_complete', 'payments_reconciled',
                'refunds_reconciled', 'renewal_dues_complete')
    if any(data['coverage'].get(k) is not True for k in required):
        raise ValueError('Incomplete coverage: do not interpret unknown data as zero')
    accounts, payments, dues = data['accounts'], data['payments'], data['renewal_dues']
    for rows in (accounts, payments, dues):
        unique(rows, 'id')
    by_user = {a['id']: a for a in accounts}
    events = ('first_hunt_at', 'first_match_view_at', 'push_registered_at')
    for a in accounts:
        if type(a['is_test']) is not bool:
            raise ValueError('is_test must be explicitly true or false')
        created = timestamp(a['created_at'])
        if not created or created > as_of:
            raise ValueError('Invalid account creation timestamp')
        for k in events:
            t = timestamp(a[k])
            if t and not created <= t <= as_of:
                raise ValueError('Milestone outside account lifetime/snapshot')
        start, end = timestamp(a['trial_started_at']), timestamp(a['trial_ends_at'])
        if bool(start) != bool(end) or (start and not created <= start <= as_of) or (start and end <= start):
            raise ValueError('Trial needs actual start and effective end')
        if start and not a['trial_cohort']:
            raise ValueError('Trial cohort required; distinguish legacy, short and extended')
    by_payment, per_user = {}, defaultdict(list)
    for p in payments:
        if p['user_id'] not in by_user:
            raise ValueError('Unmatched payment: reconcile before reporting')
        paid = timestamp(p['paid_at'])
        if not paid or not timestamp(by_user[p['user_id']]['created_at']) <= paid <= as_of:
            raise ValueError('Payment outside account lifetime/snapshot')
        if (type(p['amount_minor']) is not int or type(p['refunded_minor']) is not int
                or not 0 <= p['refunded_minor'] <= p['amount_minor'] or p['amount_minor'] <= 0):
            raise ValueError('Amounts must be positive integer minor units; refunds cannot exceed payment')
        if type(p['disputed']) is not bool or not isinstance(p['currency'], str) or len(p['currency']) != 3 or not p['currency'].isupper():
            raise ValueError('Explicit dispute status and uppercase currency required')
        if p['product'] not in ('pass', 'solo', 'kickstart', 'pro', 'elite') or p['kind'] not in ('initial', 'renewal'):
            raise ValueError('Use reconciled product and payment kind')
        if p['product'] == 'pass' and (p['kind'] == 'renewal' or p['subscription_id']):
            raise ValueError('Hunt Pass is not recurring')
        if p['product'] != 'pass' and not p['subscription_id']:
            raise ValueError('Recurring payment needs subscription_id')
        by_payment[p['id']] = p
        per_user[p['user_id']].append(p)
    for rows in per_user.values():
        rows.sort(key=lambda p: timestamp(p['paid_at']))
    seen_cycles, assigned_payments = set(), set()
    for d in dues:
        if d['user_id'] not in by_user or not d['subscription_id'] or not timestamp(d['due_at']):
            raise ValueError('Invalid renewal due')
        cycle = (d['subscription_id'], d['due_at'])
        if cycle in seen_cycles:
            raise ValueError('Duplicate renewal cycle')
        seen_cycles.add(cycle)
        if d['payment_id']:
            p = by_payment.get(d['payment_id'])
            if not p or p['kind'] != 'renewal' or p['user_id'] != d['user_id'] or p['subscription_id'] != d['subscription_id']:
                raise ValueError('Renewal payment does not match due cycle')
            if p['id'] in assigned_payments:
                raise ValueError('Renewal payment assigned more than once')
            assigned_payments.add(p['id'])
    users = [a for a in accounts if not a['is_test']]
    real_ids = {a['id'] for a in users}
    real_payments = [p for p in payments if p['user_id'] in real_ids]
    mature_signups = [a for a in users if timestamp(a['created_at']) + timedelta(days=7) <= as_of]
    activation = {}
    for k in events:
        if data['coverage'].get(k) is not True:
            activation[k] = {'status': 'unavailable', 'reason': 'Incomplete milestone coverage'}
            continue
        n = sum(bool(a[k]) and timestamp(a[k]) <= timestamp(a['created_at']) + timedelta(days=7) for a in mature_signups)
        activation[k] = ratio(n, len(mature_signups))
    cohorts = defaultdict(lambda: {'eligible': 0, 'converted': 0, 'immature': 0, 'pretrial_payer': 0})
    for a in users:
        if not a['trial_started_at']:
            continue
        c = cohorts[a['trial_cohort']]
        start, end = timestamp(a['trial_started_at']), timestamp(a['trial_ends_at'])
        first = per_user[a['id']][0] if per_user[a['id']] else None
        if first and timestamp(first['paid_at']) < start:
            c['pretrial_payer'] += 1
        elif end + timedelta(days=7) > as_of:
            c['immature'] += 1
        else:
            c['eligible'] += 1
            c['converted'] += int(bool(first) and start <= timestamp(first['paid_at']) <= end + timedelta(days=7))
    for c in cohorts.values():
        c['conversion'] = ratio(c['converted'], c['eligible'])
    firsts = [per_user[a['id']][0] for a in users if per_user[a['id']]]
    mature_firsts = [p for p in firsts if timestamp(p['paid_at']) + timedelta(days=15) <= as_of]
    retained = [p for p in mature_firsts if not p['disputed'] and p['refunded_minor'] < p['amount_minor']]
    mature_dues = [d for d in dues if d['user_id'] in real_ids and timestamp(d['due_at']) + timedelta(days=7) <= as_of]
    renewed = sum(bool(d['payment_id']) and timestamp(by_payment[d['payment_id']]['paid_at']) <= timestamp(d['due_at']) + timedelta(days=7) for d in mature_dues)
    revenue = defaultdict(lambda: {'gross_minor': 0, 'refund_minor': 0, 'disputed_gross_minor': 0})
    for p in real_payments:
        r = revenue[p['currency']]
        r['gross_minor'] += p['amount_minor']
        r['refund_minor'] += p['refunded_minor']
        if p['disputed']:
            r['disputed_gross_minor'] += p['amount_minor']
    sources = defaultdict(lambda: {'accounts': 0, 'ever_payers': 0})
    for a in users:
        row = sources[a.get('source') or 'unknown']
        row['accounts'] += 1
        row['ever_payers'] += int(bool(per_user[a['id']]))
    return {
        'as_of': data['as_of'], 'accounts': len(users), 'test_accounts_excluded': len(accounts) - len(users),
        'signup_7d': {'eligible': len(mature_signups), 'immature': len(users) - len(mature_signups), 'milestones': activation},
        'trial_cohorts': dict(cohorts),
        'first_payment_15d': {'retained_after_observed_refunds': ratio(len(retained), len(mature_firsts)),
                             'immature': len(firsts) - len(mature_firsts),
                             'partial_refunds_retained': sum(p['refunded_minor'] > 0 for p in retained)},
        'renewal_due_plus_7d': ratio(renewed, len(mature_dues)),
        'payments_by_currency': dict(revenue), 'source_descriptive_only': dict(sources),
        'limitations': ['Observed payment success is not future retention.',
                       'Refund/dispute state must match as_of; do not backdate a current ledger.',
                       'Milestones are parallel account attributes, not a sequential funnel.',
                       'No MRR, profit, CAC or ROAS inference; Pass is one-time and currencies are separate.',
                       'No historical recovery of unrecorded match views; incomplete coverage must fail.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(analyze(json.loads(args.input.read_text())), indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')
