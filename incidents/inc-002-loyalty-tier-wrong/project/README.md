# Loyalty Rewards Service

Assigns a loyalty tier to every member from their trailing-12-month points
balance, and renders the nightly member roster report.

    python -m loyalty data/members.csv
    pytest -q

Tier minimums (a member qualifies once their points reach the minimum):

| Tier     | Minimum points |
|----------|-----------------|
| Bronze   | 0               |
| Silver   | 1000            |
| Gold     | 5000            |
| Platinum | 20000           |

Member rows are `member_id,name,points`.
