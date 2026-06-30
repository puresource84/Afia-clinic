import logging

_logger = logging.getLogger(__name__)

# Universal (1-32) -> FDI two-digit mapping.
# Universal numbers run 1-16 upper right->upper left, 17-32 lower left->lower right.
UNIVERSAL_TO_FDI = {
    1: '18', 2: '17', 3: '16', 4: '15', 5: '14', 6: '13', 7: '12', 8: '11',
    9: '21', 10: '22', 11: '23', 12: '24', 13: '25', 14: '26', 15: '27', 16: '28',
    17: '38', 18: '37', 19: '36', 20: '35', 21: '34', 22: '33', 23: '32', 24: '31',
    25: '41', 26: '42', 27: '43', 28: '44', 29: '45', 30: '46', 31: '47', 32: '48',
}


def post_init_hook(env):
    """Migrate legacy teeth.chart boolean records into dental.tooth.record.

    The legacy model stores a patient name and 32 booleans. Marked teeth are
    imported as 'caries' (legacy semantics: 'tooth flagged for attention')
    with a note pointing back to the source record. Patients are matched by
    exact name among is_patient partners; unmatched charts are logged and
    skipped, never guessed.
    """
    if 'teeth.chart' not in env:
        _logger.info('Legacy teeth.chart model not installed; nothing to migrate.')
        return
    ToothRecord = env['dental.tooth.record']
    Partner = env['res.partner']
    migrated = skipped = 0
    for chart in env['teeth.chart'].search([]):
        patient = Partner.search(
            [('is_patient', '=', True), ('name', '=', chart.name)], limit=2)
        if len(patient) != 1:
            _logger.warning(
                'teeth.chart #%s: %s matching patients for name %r — skipped.',
                chart.id, len(patient) or 'no', chart.name)
            skipped += 1
            continue
        for universal, fdi in UNIVERSAL_TO_FDI.items():
            if not getattr(chart, 'tooth_%d' % universal, False):
                continue
            exists = ToothRecord.search_count([
                ('patient_id', '=', patient.id), ('tooth_fdi', '=', fdi)])
            if exists:
                continue
            ToothRecord.create({
                'patient_id': patient.id,
                'tooth_fdi': fdi,
                'condition': 'caries',
                'notes': 'Migrated from legacy teeth chart #%d '
                         '(universal tooth %d). Verify condition.' % (chart.id, universal),
            })
        migrated += 1
    _logger.info('Legacy teeth chart migration: %d charts migrated, %d skipped.',
                 migrated, skipped)
