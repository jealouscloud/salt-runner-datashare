# data share salt-runner

Copy and share data between salt minions.

Most useful in Salt orchestrator.

Add to master conf:

```yaml
---
gitfs_remotes:
  - git@github.com:jealouscloud/salt-runner-datashare.git:
    - base: main
    - root: src
```

# Usage
Example copying file between hosts

```yaml
Share /var/cache/linstor_db.path with {{ node }}:
  salt.runner:
    - name: datashare.use
    - src:
        id: {{ caller | yaml_dquote}}
        cmd: file.read
        kwargs:
          path: /var/cache/linstor_db.path
    - target:
        id: {{ node | yaml_dquote }}
        cmd: file.write
        args:
          - /var/cache/linstor_db.path
          - __DATA__ # content arg. data read from src is written to anywhere __DATA__ is used.
    - require:
      - Bootstrap cluster
```