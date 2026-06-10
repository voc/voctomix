from typing import Iterable

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily, UnknownMetricFamily

from vocto.port import Port
import voctocore.lib.pipeline

from prometheus_client.registry import Collector
from prometheus_client import Metric, start_http_server

import logging

from voctocore.lib.config import Config


class Metrics(Collector):
    log: logging.Logger
    pipeline: 'voctocore.lib.pipeline.Pipeline'

    def __init__(self, pipeline):
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('Metrics')

        self.pipeline = pipeline
        self.server, self.server_thread = None, None

    def start(self):
        self.log.info('Starting metrics server...')
        self.server, self.server_thread = start_http_server(Port.METRICS)

    def stop(self):
        if self.server:
            self.log.info('Shutting down metrics server...')
            self.server.shutdown()
            self.server.server_close()

    def collect(self) -> Iterable[Metric]:
        sources = Config.getSources()

        source_info = UnknownMetricFamily(
            f'voctocore_source',
            f'Info about a source',
            labels=['port', 'name']
        )

        for idx, source_name in enumerate(sources):
            port = Port.SOURCES_IN + idx
            source_info.add_metric([str(port), source_name], 1)

        yield source_info
