# Simple tracking of benchmark results across git commits

## Commands

### init

Initializes configuration files in the local git repository.

There are two config giles:

| path   | Tracked by git | Contents |
| -------- | ------- | --- |
| *.benchk/repo_config.yml*  | yes | How to build and run benchmarks       |
| *.benchk/local_config.yml* | no  | Local machine config and state of app |

---

### benchmark

Run benchmarks (and build/test) and generate a report in *.benchk/report.yml*

---

### list

Create a ranking of past runs by reading reports and aggregating benchmark results

Example output:
```
Comparing results for machine: MyMachine

000000023.55 [unit], 5f04eb7838, Slower
000000023.54 [unit], 7bccefda5f, First commit
000000023.53 [unit], 57b7571e64, Better (best) (current)
```