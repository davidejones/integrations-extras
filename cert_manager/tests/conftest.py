# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os

import pytest

from datadog_checks.base.utils.common import get_docker_hostname
from datadog_checks.dev import run_command
from datadog_checks.dev.kind import kind_run
from datadog_checks.dev.kube_port_forward import port_forward

try:
    from contextlib import ExitStack
except ImportError:
    from contextlib2 import ExitStack


HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 9402

def setup_cert_manager():

    run_command(["kubectl", "apply", "-f", "https://github.com/jetstack/cert-manager/releases/download/v1.2.0/cert-manager.yaml"])
    run_command(
        ["kubectl", "wait", "deployments", "--all", "--for=condition=Available", "-n", "cert-manager", "--timeout=300s"]
    )
    run_command(["kubectl", "wait", "pods", "-n", "cert-manager", "--all", "--for=condition=Ready", "--timeout=300s"])
    config = os.path.join(HERE, 'kubernetes', 'test-resources.yaml')
    run_command(["kubectl", "create", "-f", config])
    run_command(["kubectl", "wait", "certificates", "-n", "cert-manager-test", "--all", "--for=condition=Ready", "--timeout=300s"])

@pytest.fixture(scope='session')
def dd_environment():
    with kind_run(conditions=[setup_cert_manager]) as kubeconfig:
        with ExitStack() as stack:
            ip_ports = [
                stack.enter_context(port_forward(kubeconfig, 'cert-manager', 'cert-manager', PORT))
            ]
        instances = {
            'instances': [
                {'prometheus_url': 'http://{}:{}/metrics'.format(*ip_ports[0])},
            ]
        }

        yield instances

@pytest.fixture
def instance():
    return {}
