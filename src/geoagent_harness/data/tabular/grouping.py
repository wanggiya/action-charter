"""Pure grouped percentages with complete-population denominators."""


def percentages(groups, keys, matched):
    totals = {}
    for row in groups:
        totals[row[keys[0]]] = totals.get(row[keys[0]], 0) + row['row_count']
    return [{**{k:r[k] for k in keys}, 'row_count':r['row_count'],
             'total_denominator':matched, 'primary_denominator':totals[r[keys[0]]],
             'percentage_total':100*r['row_count']/matched if matched else None,
             'percentage_within_primary':100*r['row_count']/totals[r[keys[0]]] if totals[r[keys[0]]] else None}
            for r in groups]
