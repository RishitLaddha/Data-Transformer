"""
Agent 4 – Multi‑header flattener
Re‑usable function that converts a stacked‑header Excel sheet
into a long, tidy DataFrame and writes it to an .xlsx file.
"""

import pandas as pd


def convert_multi_to_long(input_path: str, output_path: str = "output.xlsx") -> None:
    """
    Parameters
    ----------
    input_path : str
        Path to the source Excel file that contains stacked header rows.
    output_path : str, default "output.xlsx"
        Where to save the flattened result.
    """
    # ──────────────────────────────────────────────
    # 1. Load **raw** sheet (treat every row as data)
    # ──────────────────────────────────────────────
    df = pd.read_excel(input_path, header=None, dtype=str)

    # ──────────────────────────────────────────────
    # 2. Locate first data row (first cell looks numeric)
    # ──────────────────────────────────────────────
    first_data_row = next(
        i
        for i, v in enumerate(df.iloc[:, 0].fillna("").astype(str))
        if v.replace(",", "").isdigit()
    )

    # Row just above = contains the labels for the static identifier columns
    id_header_row = first_data_row - 1
    id_headers = df.iloc[id_header_row, :2].tolist()  # assume first two are static

    # ──────────────────────────────────────────────
    # 3. Harvest metadata rows (stacked headers)
    # ──────────────────────────────────────────────
    meta_rows = df.iloc[:id_header_row]
    meta = {
        str(row[0]).strip(): row.iloc[2:].tolist()          # label : list‑of‑values
        for _, row in meta_rows.iterrows()
        if str(row[0]).strip()                              # ignore fully blank
    }

    # ──────────────────────────────────────────────
    # 4. Walk through every student row, every mark cell
    # ──────────────────────────────────────────────
    records = []
    for _, s_row in df.iloc[first_data_row:].iterrows():
        if s_row.isna().all():
            continue

        for col_idx in range(2, df.shape[1]):  # dynamic mark columns start at 2
            mark = s_row[col_idx]
            if pd.isna(mark) or str(mark).strip() == "":
                continue

            entry = {
                id_headers[0]: s_row[0],   # ID
                id_headers[1]: s_row[1],   # Name
                "Marks": mark,
            }

            # attach metadata for this column (same positional index)
            for label, values in meta.items():
                if col_idx - 2 < len(values):
                    entry[label] = values[col_idx - 2]

            records.append(entry)

    # ──────────────────────────────────────────────
    # 5. Save output
    # ──────────────────────────────────────────────
    output_df = pd.DataFrame(records)
    output_df.to_excel(output_path, index=False)
    print(output_df.to_string(index=False))