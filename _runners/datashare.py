"""
Salt runner for shuffling data between minions
"""

import logging
import yaml
import salt.client
from salt.exceptions import ArgumentValueError, SaltClientError

log = logging.getLogger(__name__)


def use(
    src: dict,
    target: dict,
    timeout=10,
    omit_ret=True,
    search_string="__DATA__",
):
    """
    Run a command on src and write its output to a command on target

    The transferred data must be referred to in the target cmomand by
    seach_string. This is __DATA__ by default
    """
    client = salt.client.LocalClient(__opts__["conf_file"])
    for v in ["cmd", "id"]:
        if v not in src or v not in target:
            raise ArgumentValueError(f"Must provide '{v}' in src/target")

    def run_cmd(tgt):
        tgt_id = tgt.get("id")
        tgt_cmd = tgt.get("cmd")
        tgt_args = tgt.get("args", [])
        tgt_kwargs = tgt.get("kwargs", {})

        # Run salt command on src.id
        result = client.cmd(
            tgt_id,
            tgt_cmd,
            arg=tgt_args,
            kwarg=tgt_kwargs,
            timeout=timeout,
            full_return=True,
        )
        result = result[tgt_id]

        if result["retcode"] != 0:
            log.error(
                f"Salt command {tgt_cmd} on {tgt_id} returned {result['retcode']}"
            )

        return result

    src_result = run_cmd(src)
    if src_result["retcode"] != 0:

        raise SaltClientError(
            f"Non-zero status returned for {src['cmd']=}. \n{yaml.dump(src_result)}"
        )

    shared_data = src_result["ret"]

    def find_and_replace(data):
        if isinstance(data, dict):
            return {key: find_and_replace(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [find_and_replace(item) for item in data]
        elif isinstance(data, str) and search_string in data:
            return data.replace(search_string, shared_data)
        else:
            return data  # No replacement needed for other types

    if "args" in target:
        target["args"] = find_and_replace(target["args"])

    if "kwargs" in target:
        target["kwargs"] = find_and_replace(target["kwargs"])

    tgt_result = run_cmd(target)

    if tgt_result["retcode"] != 0:
        raise SaltClientError(
            f"Non-zero status returned for {target['cmd']=}. \n{yaml.dump(tgt_result)}"
        )

    if omit_ret:
        tgt_result.pop("ret")
        src_result.pop("ret")
    src_result["cmd"] = src["cmd"]
    tgt_result["cmd"] = target["cmd"]
    return {
        "tgt": tgt_result,
        "src": src_result,
        "result": True,
        "comment": "Data was shimmied around",
    }
