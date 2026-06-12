from typing import Iterable

from prometheus_client.metrics_core import GaugeMetricFamily, UnknownMetricFamily

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
            'voctocore_source',
            'Info about a source',
            labels=['port', 'name', 'kind']
        )

        for idx, source_name in enumerate(sources):
            source_port = Port.SOURCES_IN + idx
            kind = Config.getSourceKind(source_name)
            source_info.add_metric([str(source_port), source_name, kind], 1)

        yield source_info

        queue_info = GaugeMetricFamily(
            'voctocore_gst_queue',
            'Info about a queue',
            labels=['name', 'property'],
        )

        for queue_item in self.pipeline.queues:
            for prop in ['current-level-time']:
                value = queue_item.get_property(prop)
                queue_info.add_metric([queue_item.name, prop], value)

        yield queue_info

        port_info = UnknownMetricFamily(
            'voctocore_port',
            'Info about a port',
            labels=['name', 'source', 'type', 'is_input', 'is_output']
        )

        for port in self.pipeline.ports:
            port_source = '<NONE>'

            if port.source and hasattr(port.source, 'source'):
                port_source = port.source.source

            port_type = type(port.source).__name__

            port_info.add_metric([port.name, port_source, port_type, str(int(port.is_input())), str(int(port.is_output()))], 1)

        yield port_info

        port_connections = GaugeMetricFamily(
            'voctocore_port_connections',
            'Connections of a port',
            labels=['name', 'is_input', 'is_output']
        )

        for port in self.pipeline.ports:
            port_connections.add_metric([port.name, str(int(port.is_input())), str(int(port.is_output()))], port.connections)

        yield port_connections

        if Config.getBlinderEnabled():
            blinder_metric = GaugeMetricFamily(
                'voctocore_blinder',
                '1 if live, 0 if blinded',
                labels=['blind_source']
            )

            blind_source = self.pipeline.blinder.blind_source
            if blind_source is None:
                blinder_metric.add_metric([''], 1)
            else:
                blinder_metric.add_metric([self.pipeline.blinder.blindersources[blind_source]], 0)

            yield blinder_metric

        current_composite = UnknownMetricFamily(
            'voctocore_current_composite',
            'The current composite of sources',
            labels=['composite', 'a', 'b']
        )

        if self.pipeline.vmix.compositeMode is not None and self.pipeline.vmix.sourceA is not None and self.pipeline.vmix.sourceB is not None:
            current_composite.add_metric([
                self.pipeline.vmix.compositeMode,
                self.pipeline.vmix.sourceA,
                self.pipeline.vmix.sourceB
            ], 1)

        yield current_composite
