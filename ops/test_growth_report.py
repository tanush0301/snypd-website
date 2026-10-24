"""Run: python -m unittest discover -s ops -p test_growth_report.py"""
import copy
import unittest
from growth_report import analyze


def account(id='a', **kwargs):
    return dict(id=id, created_at='2026-10-01T00:00:00Z', is_test=False, source=None,
                first_hunt_at='2026-10-02T00:00:00Z', first_match_view_at=None,
                push_registered_at=None, trial_started_at='2026-10-02T00:00:00Z',
                trial_ends_at='2026-10-05T00:00:00Z', trial_cohort='72h', **kwargs)


def payment(id='p', **kwargs):
    p = dict(id=id, user_id='a', paid_at='2026-10-04T00:00:00Z', amount_minor=399,
             refunded_minor=0, disputed=False, currency='EUR', product='pass',
             kind='initial', subscription_id=None)
    p.update(kwargs)
    return p


def fixture():
    return dict(schema_version=1, as_of='2026-10-24T00:00:00Z',
                coverage={k: True for k in ('accounts_complete', 'payments_reconciled',
                    'refunds_reconciled', 'renewal_dues_complete', 'first_hunt_at',
                    'push_registered_at', 'first_match_view_at')},
                accounts=[account()], payments=[payment()], renewal_dues=[])


class GrowthReportTests(unittest.TestCase):
    def test_mature_conversion(self):
        r = analyze(fixture())
        self.assertEqual(r['trial_cohorts']['72h']['conversion']['percent'], 100)
        self.assertEqual(r['first_payment_15d']['retained_after_observed_refunds']['percent'], 100)
        self.assertIsNone(r['renewal_due_plus_7d']['percent'])

    def test_immature_trial_excluded(self):
        d = fixture(); d['accounts'][0]['trial_ends_at'] = '2026-10-20T00:00:00Z'
        c = analyze(d)['trial_cohorts']['72h']
        self.assertEqual(c['immature'], 1); self.assertIsNone(c['conversion']['percent'])

    def test_pretrial_payment_excluded(self):
        d = fixture(); d['payments'][0]['paid_at'] = '2026-10-01T12:00:00Z'
        c = analyze(d)['trial_cohorts']['72h']
        self.assertEqual(c['pretrial_payer'], 1); self.assertEqual(c['eligible'], 0)

    def test_payment_outside_window(self):
        d = fixture(); d['payments'][0]['paid_at'] = '2026-10-13T00:00:00Z'
        r = analyze(d)
        self.assertEqual(r['trial_cohorts']['72h']['converted'], 0)
        self.assertEqual(r['first_payment_15d']['immature'], 1)

    def test_refund_and_dispute(self):
        for changes in ({'refunded_minor':399}, {'disputed':True}):
            d = fixture(); d['payments'][0].update(changes)
            self.assertEqual(analyze(d)['first_payment_15d']['retained_after_observed_refunds']['numerator'], 0)
        d = fixture(); d['payments'][0]['refunded_minor'] = 100
        self.assertEqual(analyze(d)['first_payment_15d']['partial_refunds_retained'], 1)

    def test_excludes_test_accounts(self):
        d = fixture(); d['accounts'][0]['is_test'] = True
        r = analyze(d)
        self.assertEqual(r['accounts'], 0); self.assertEqual(r['payments_by_currency'], {})

    def test_rejects_unmatched_or_duplicate_payments(self):
        d = fixture(); d['payments'].append(copy.deepcopy(d['payments'][0]))
        with self.assertRaises(ValueError): analyze(d)
        d = fixture(); d['payments'][0]['user_id'] = 'missing'
        with self.assertRaises(ValueError): analyze(d)

    def test_incomplete_coverage(self):
        d = fixture(); d['coverage']['payments_reconciled'] = False
        with self.assertRaises(ValueError): analyze(d)
        d = fixture(); d['coverage']['first_match_view_at'] = False
        self.assertEqual(analyze(d)['signup_7d']['milestones']['first_match_view_at']['status'], 'unavailable')

    def test_renewal_requires_due_cycle(self):
        d = fixture()
        d['payments'].append(payment('r', paid_at='2026-10-15T00:00:00Z', product='solo', kind='renewal', subscription_id='s'))
        d['renewal_dues'] = [dict(id='d', user_id='a', subscription_id='s', due_at='2026-10-14T00:00:00Z', payment_id='r')]
        self.assertEqual(analyze(d)['renewal_due_plus_7d']['percent'], 100)
        d['renewal_dues'][0]['due_at'] = '2026-10-23T00:00:00Z'
        self.assertIsNone(analyze(d)['renewal_due_plus_7d']['percent'])

    def test_pass_not_recurring(self):
        d = fixture(); d['payments'][0]['kind'] = 'renewal'
        with self.assertRaises(ValueError): analyze(d)

    def test_signup_maturity_and_late_activation(self):
        d = fixture(); d['accounts'][0]['first_hunt_at'] = '2026-10-10T00:00:00Z'
        self.assertEqual(analyze(d)['signup_7d']['milestones']['first_hunt_at']['numerator'], 0)
        d['accounts'][0].update(created_at='2026-10-23T00:00:00Z', first_hunt_at=None, trial_started_at=None, trial_ends_at=None)
        d['payments'] = []
        self.assertEqual(analyze(d)['signup_7d']['immature'], 1)

    def test_currency_separation_and_timezone_validation(self):
        d = fixture(); d['payments'].append(payment('usd', currency='USD'))
        self.assertEqual(set(analyze(d)['payments_by_currency']), {'USD','EUR'})
        d['as_of'] = '2026-10-24T00:00:00'
        with self.assertRaises(ValueError): analyze(d)


if __name__ == '__main__':
    unittest.main()
