"""Score the pipeline on a labeled folder. labels.csv columns: file,denomination,year,mint_mark,strike_type,error_type,grade
Usage: python evaluate.py labels.csv images_dir"""
import csv
import sys
from pathlib import Path

from pipeline import analyze


def main(labels_csv: str, images_dir: str):
    n = ident_ok = err_tp = err_fp = err_fn = 0
    for row in csv.DictReader(open(labels_csv)):
        rep = analyze([str(Path(images_dir) / row["file"])])
        r = rep.raw
        n += 1
        i = r["identification"]
        ident_ok += (str(i["year"]) == row["year"] and (i["mint_mark"] or "") == row["mint_mark"]
                     and (i["denomination"] or "").lower() == row["denomination"].lower())
        pred_err = r["error_check"]["type"] not in ("none", "unsure")
        true_err = row["error_type"] not in ("", "none")
        err_tp += pred_err and true_err
        err_fp += pred_err and not true_err
        err_fn += (not pred_err) and true_err
    prec = err_tp / (err_tp + err_fp) if err_tp + err_fp else float("nan")
    rec = err_tp / (err_tp + err_fn) if err_tp + err_fn else float("nan")
    print(f"n={n} id_exact={ident_ok / n:.2%} error_precision={prec:.2%} error_recall={rec:.2%}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
