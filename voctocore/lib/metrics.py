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

    def start(self, port=20000):
        self.log.info('Starting metrics server...')
        self.server, self.server_thread = start_http_server(port)

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
            labels=['port', 'name', 'kind']
        )

        for idx, source_name in enumerate(sources):
            port = Port.SOURCES_IN + idx
            kind = Config.getSourceKind(source_name)
            source_info.add_metric([str(port), source_name, kind], 1)

        yield source_info

        queue_info = GaugeMetricFamily(
            f'voctocore_gst_queue',
            f'Info about a queue',
            labels=['name', 'property'],
        )

        for queue_item in self.pipeline.queues:
            for prop in ['current-level-time']:
                value = queue_item.get_property(prop)
                queue_info.add_metric([queue_item.name, prop], value)

        yield queue_info
