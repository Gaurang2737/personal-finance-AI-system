import pandas as pd
from datetime import timedelta

def get_passthrough_transactions(
        df : pd.DataFrame,
        time_window_hours: int = 24,
        amount_tolerance: float = 0.2,
        min_amount: float = 1000.0
     ) -> list[dict]:
    df = df.sort_values('date').reset_index()
    credits = df[(df['type']=='Credit')&(df['is_pass_through']== False)&(df['amount']>=min_amount)]
    debits = df[(df['type']=='Debit')&(df['is_pass_through']== False)&(df['amount']>=min_amount)]

    potential_pairs = []
    used_debits_indices = set()
    for credit_idx , credit_row in credits.iterrows():
        time_window_end = credit_row['date'] + timedelta(hours=time_window_hours)

        lower_bound = credit_row['amount'] * (1-amount_tolerance)
        upper_bound = credit_row['amount'] * (1+amount_tolerance)

        possible_matches = debits[
            (debits['date']>credit_row['date'])&
            (debits['date']<=time_window_end)&
            (debits['amount']>=lower_bound)&
            (debits['amount']<=upper_bound)&
            (~debits.index.isin(used_debits_indices))
        ]

        if not possible_matches.empty:
            best_match = possible_matches.iloc[0]
            potential_pairs.append({
                'credits': credit_row.to_dict(),
                'debits': best_match.to_dict()
            })
            used_debits_indices.add(best_match.name)

    return potential_pairs



