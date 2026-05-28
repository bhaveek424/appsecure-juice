# Use SQLite For Review State

We will store scans, hypotheses, findings, evidence packets, skill runs, and reviewer dispositions in SQLite. Flat JSON files would be enough for a throwaway scanner demo, but this product needs persistent review state, filtering, sorting, history, and partial updates without introducing a separate database service; SQLite gives us that middle ground.
