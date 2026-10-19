# Validation

Prepared October 19, 2026 from the latest guided-clickable studio revision.

Test environment: Windows, Python 3.13.9, Streamlit 1.51.0. The 18-test suite verifies lecture benchmarks, binomial sums, pricing/discounting with yield, put-call parity, American exercise, compound gates, restricted expressions, all routes, setup questions, resets and column-fill safety.

Chrome checks on the source studio verified node clicking, wrong-answer retry, right-to-left warnings, a complete one-period calculation, Yes/No column completion, negative gate NPV, full lattice views, all guided routes and mobile overflow.

This standalone package is also tested with the included suite. Cloud deployment has not yet been performed. Dependencies are pinned at the tested Streamlit version; transitive packages are resolved by pip.

Only runtime files, ungraded teaching content, tests and clean deployment documentation are included. Local caches, environment folders, practice downloads, machine-specific launchers, source-directory inventories and historical screenshots/logs are omitted.
