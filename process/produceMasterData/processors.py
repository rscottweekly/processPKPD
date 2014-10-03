__author__ = 'rscottweekly'

def process_plasma(df_plasma):
    df_plasma = df_plasma[pd.notnull(df_plasma['Time'])]
    combine = lambda x: datetime.datetime.combine(x['Date'].to_datetime().date(), x['Time'].to_datetime().time())

    #print type(df_plasma['Date'].to_datetime())

    #.date()#.to_datetime()#.date()
    df_plasma['DateTime'] = df_plasma.apply(combine, axis=1)

    df_plasma['Des_mol/L'] = df_plasma['Des_mmol/L'] / 1000000
    df_plasma['Sev_mol/L'] = df_plasma['Sev_mmol/L'] / 1000000

    df_plasma.set_index(['DateTime'], inplace=True)

    return df_plasma