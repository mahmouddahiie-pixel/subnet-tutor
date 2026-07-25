"""Subnetting scenario generator and deterministic grader."""

from __future__ import annotations

import ipaddress
import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"

NETWORKS = [
    "192.168.1.0/24",
    "192.168.5.0/24",
    "192.168.10.0/24",
    "10.0.0.0/24",
    "172.16.0.0/24",
    "192.168.100.0/24",
]

SUBNET_COUNTS = [2, 4, 6, 8, 10, 12, 16, 20, 25, 30]
HOST_COUNTS = [10, 14, 25, 30, 50, 60, 100, 120]


def _borrowed_bits_for_subnets(required_subnets: int) -> int:
    return math.ceil(math.log2(required_subnets))


def _host_bits_for_hosts(required_hosts: int) -> int:
    return math.ceil(math.log2(required_hosts + 2))


def _subnet_solution(network: str, borrowed_bits: int) -> dict[str, Any]:
    net = ipaddress.IPv4Network(network, strict=False)
    new_prefix = net.prefixlen + borrowed_bits
    subnet_count = 2**borrowed_bits
    subnets = list(net.subnets(new_prefix=new_prefix))
    first_subnet = subnets[0]
    host_bits = 32 - new_prefix
    usable_hosts = 2**host_bits - 2 if host_bits > 1 else 0
    block_size = 2 ** (host_bits if new_prefix > 24 else host_bits)

    if new_prefix <= 24:
        block_in_octet = 32 - new_prefix
        block_size = 2**block_in_octet if block_in_octet <= 8 else block_size

    last_octet_bits = max(0, 32 - new_prefix)
    if last_octet_bits <= 8:
        block_size = 2**last_octet_bits

    return {
        "answer_prefix": new_prefix,
        "answer_subnets": subnet_count,
        "answer_mask": str(first_subnet.netmask),
        "answer_block_size": block_size,
        "borrowed_bits": borrowed_bits,
        "usable_hosts": usable_hosts,
        "subnet_list": [str(s) for s in subnets[:min(8, len(subnets))]],
    }


def generate_subnet_count_scenario(seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    network = rng.choice(NETWORKS)
    required = rng.choice(SUBNET_COUNTS)
    borrowed = _borrowed_bits_for_subnets(required)
    solution = _subnet_solution(network, borrowed)

    return {
        "level": 1,
        "type": "subnet_count",
        "network": network,
        "requirement": "at_least_n_subnets",
        "required_value": required,
        "prompt_key": "game_level1_prompt",
        **solution,
    }


def generate_host_count_scenario(seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    network = rng.choice(NETWORKS)
    required_hosts = rng.choice(HOST_COUNTS)
    host_bits = _host_bits_for_hosts(required_hosts)
    new_prefix = 32 - host_bits
    net = ipaddress.IPv4Network(network, strict=False)
    borrowed = new_prefix - net.prefixlen
    solution = _subnet_solution(network, borrowed)
    solution["required_hosts"] = required_hosts
    solution["host_bits"] = host_bits

    return {
        "level": 2,
        "type": "host_count",
        "network": network,
        "requirement": "at_least_n_hosts",
        "required_value": required_hosts,
        "prompt_key": "game_level2_prompt",
        **solution,
    }


def generate_assignment_scenario(seed: int | None = None) -> dict[str, Any]:
    base = generate_subnet_count_scenario(seed)
    rng = random.Random(seed)
    subnets = base["subnet_list"]
    target_subnet = rng.choice(subnets)
    subnet_net = ipaddress.IPv4Network(target_subnet, strict=False)
    hosts = list(subnet_net.hosts())
    if len(hosts) < 3:
        return generate_assignment_scenario((seed or 0) + 1)

    device_count = min(3, len(hosts))
    devices = [
        {"name": f"PC-{i+1}", "ip": str(hosts[i])}
        for i in range(device_count)
    ]

    return {
        **base,
        "level": 3,
        "type": "ip_assignment",
        "prompt_key": "game_level3_prompt",
        "target_subnet": target_subnet,
        "devices": devices,
        "answer_subnet": target_subnet,
    }


def generate_freeform_scenario(seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    if rng.random() < 0.5:
        scenario = generate_subnet_count_scenario(seed)
    else:
        scenario = generate_host_count_scenario(seed)
    scenario["level"] = 4
    scenario["type"] = "freeform"
    scenario["prompt_key"] = "game_level4_prompt"
    return scenario


def generate_scenario(level: int, seed: int | None = None) -> dict[str, Any]:
    generators = {
        1: generate_subnet_count_scenario,
        2: generate_host_count_scenario,
        3: generate_assignment_scenario,
        4: generate_freeform_scenario,
    }
    return generators[level](seed)


def grade_subnet_answer(scenario: dict[str, Any], user_answer: dict[str, Any]) -> dict[str, Any]:
    correct = True
    details: list[str] = []

    def _parse_int(field: str, raw: Any) -> int | None:
        nonlocal correct
        if raw is None or raw == "":
            return None
        text = str(raw).strip().lstrip("/")
        try:
            return int(text)
        except (TypeError, ValueError):
            correct = False
            details.append(f"Invalid {field} format")
            return None

    if "prefix" in user_answer:
        prefix = _parse_int("prefix", user_answer["prefix"])
        if prefix is not None and prefix != scenario["answer_prefix"]:
            correct = False
            details.append(
                f"Prefix should be /{scenario['answer_prefix']}, not /{user_answer['prefix']}"
            )

    if "subnets" in user_answer:
        subnets = _parse_int("subnets", user_answer["subnets"])
        if subnets is not None and subnets != scenario["answer_subnets"]:
            correct = False
            details.append(
                f"Subnet count should be {scenario['answer_subnets']}, not {user_answer['subnets']}"
            )

    if "block_size" in user_answer:
        block_size = _parse_int("block_size", user_answer["block_size"])
        if block_size is not None and block_size != scenario["answer_block_size"]:
            correct = False
            details.append(
                f"Block size should be {scenario['answer_block_size']}, not {user_answer['block_size']}"
            )

    if "mask" in user_answer:
        expected = scenario["answer_mask"]
        try:
            if str(ipaddress.IPv4Address(user_answer["mask"])) != expected:
                correct = False
                details.append(f"Mask should be {expected}")
        except ipaddress.AddressValueError:
            correct = False
            details.append("Invalid mask format")

    if "subnet" in user_answer and "answer_subnet" in scenario:
        if user_answer["subnet"] != scenario["answer_subnet"]:
            correct = False
            details.append(f"Correct subnet is {scenario['answer_subnet']}")

    if "fingers" in user_answer:
        fingers = _parse_int("fingers", user_answer["fingers"])
        if fingers is not None and fingers != scenario["borrowed_bits"]:
            correct = False
            details.append(
                f"Raise {scenario['borrowed_bits']} fingers (2^{scenario['borrowed_bits']} = {scenario['answer_subnets']} subnets)"
            )

    return {"correct": correct, "details": details, "expected": {
        "prefix": scenario.get("answer_prefix"),
        "subnets": scenario.get("answer_subnets"),
        "block_size": scenario.get("answer_block_size"),
        "mask": scenario.get("answer_mask"),
        "subnet": scenario.get("answer_subnet"),
        "fingers": scenario.get("borrowed_bits"),
    }}


def load_worked_problems() -> list[dict[str, Any]]:
    path = KNOWLEDGE_DIR / "worked_problems.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
