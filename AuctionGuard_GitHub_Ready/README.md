# AuctionGuard 3.0 — Explainable Auction Bidding-Pattern Screening

**Author:** Ali Raza | **Research and development context:** AR Autos Perth  
**Repository preparation:** November 2026. The repository is a public-facing release of available code; its creation date is **not** evidence of earlier Git commits.

## Overview

AuctionGuard is a **local Python research prototype** for exploratory screening of online auction bidding histories. It highlights predefined behavioural indicators, provides bid-level explanations and allows reviewers to export screening outputs. Flags are **not fraud verdicts** and must not be interpreted as calibrated probabilities.

This repository contains two distinct components:

1. `app/` — **rule-based** local browser application (AuctionGuard 3.0), with a synthetic demonstration dataset.
2. `research/` — a **separate** reproducible synthetic experiment comparing a predefined rule baseline, Isolation Forest and Random Forest on simulator-assigned scenario labels.

**Important:** The app does not implement machine-learning classification, SHAP/LIME or blockchain. Those methods are not features of the current screening application.

## Run the application

Requirements: Python 3 (the CSV-based application uses the Python standard library).

```bash
cd app
python3 app.py
```

Then visit http://127.0.0.1:8765 and click **Use synthetic demo**. To stop, use Ctrl+C.

You can also import your own compatible auction CSV files. The required columns are:

`Auction ID, Lot, Pseudonym, Bid Date (DD/MM/YYYY), Bid Time (local as shown), Bid AUD`

The optional auction register may include `Reported Bids` and `Source PDF`. Experimental text-based PDF importing requires `pdfplumber`, installed separately (`python3 -m pip install pdfplumber`). Image-only PDFs are not supported by built-in OCR. Review parsed data before interpretation.

The app binds only to `127.0.0.1`. It does not submit records to a cloud service. Avoid using sensitive or confidential bid histories without permission.

## Reproduce the synthetic research experiment

Requirements: Python 3 with scikit-learn and numpy.

```bash
python3 -m pip install numpy scikit-learn
cd research
python3 experiment.py
```

The script generates 100 synthetic auction summaries using a fixed seed (`20261021`), with 80 training and 20 test cases, and overwrites three CSV output files in `research/`:

- `synthetic_cases.csv`: generated feature values and artificial labels
- `synthetic_comparison_results.csv`: precision, recall, F1 and confusion-matrix counts
- `test_predictions.csv`: individual held-out labels and predictions

Recorded synthetic test-set results:

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| Predefined rule baseline | 1.000 | 1.000 | 1.000 |
| Isolation Forest | 0.769 | 1.000 | 0.870 |
| Random Forest | 1.000 | 1.000 | 1.000 |

High scores are expected on simplified, generated data. **No confirmed real-world fraud labels were used**, and the results do not demonstrate deployed fraud-detection accuracy. The generator-defined labels and rule thresholds are related by construction, so these results should not be treated as an independent benchmark.

## Research limitations

- Anomalous or rapid bidding may be legitimate; it does not prove shill bidding.
- Auction data can omit bids, timestamps or context.
- Synthetic ground truth is artificial; real-world classification performance is unknown.
- Bidder aliases cannot establish real-world identity or collusion.
- This code does **not** reproduce the original 2025 Master's experiments, which are not available in this repository.
- The research documentation is retrospective. The repository does not itself independently verify earlier employment or research hours.

## Data provenance and exclusions

The original working archive also contained extracted Grays auction records and a contextual evidence brief. Those are **not included in this public-facing package** because of third-party data reuse and personal-context considerations. The bundled examples here are explicitly synthetic. The **Use included Grays sample** control has therefore been removed from this release, while user-supplied CSV/PDF import remains available.

## Copyright and use

Copyright © 2026 Ali Raza. **All rights reserved.** No open-source licence is granted by the absence of a licence file. Contact the author for reuse permission. Repository visibility can be public while source reuse rights remain reserved.
