# ASO-X Policy Matrix

| Action class | Automation level | Human approval |
|---|---:|---:|
| Read repo state | Allowed | No |
| Generate docs/tests | Allowed | No |
| Run validation | Allowed | No |
| Create branch | Assisted | Optional |
| Open PR | Assisted | Optional |
| Merge PR | Manual/assisted | Yes |
| Production money movement | Blocked by default | Yes |
| Credential or secret change | Blocked by default | Yes |
| Destructive git history change | Blocked by default | Yes |
