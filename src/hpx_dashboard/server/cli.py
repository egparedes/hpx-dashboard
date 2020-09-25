# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause


"""Main entry for the hpx dashboard server
"""

import argparse
from queue import Queue
import sys
import threading

from tornado.ioloop import IOLoop

from ..common.logger import Logger
from .tcp_listener import TCP_Server, handle_response
from .worker import worker_thread, WorkerQueue
from .data import DataAggregator
from .app import bk_server


def args_parse(argv):
    """Parses the argument list"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-pl",
        "--listen-port",
        dest="listen_port",
        help="port on which the server listens for the incoming parsed data "
        "generated by the hpx-dashboard agent.",
        default=5267,
    )

    parser.add_argument(
        "-pb",
        "--bokeh-port",
        dest="bokeh_port",
        help="port on which the server starts the Bokeh server for the live plotting.",
        default=5006,
    )

    parser.add_argument(
        "--no-auto-save",
        dest="no_save",
        help="Disable auto-save feature of sessions.",
        default=False,
    )

    parser.add_argument(
        "-s",
        "--save-path",
        dest="save_path",
        help="Path where the session will be auto-saved.The hpx-dashboard server creates a folder"
        " with a timestamp where all the data will be saved as csv format.",
        default="",
    )

    parser.add_argument(
        "-i",
        "--import-path",
        dest="import_path",
        help="Path to a folder containing an existing session which will be imported. Additional"
        " collections will be saved to the folder. The folder shoud have been created by the"
        " hpx-dashboard server. If the import failed, then a normal new session is created.",
        default=None,
    )

    return parser.parse_args(argv)


def server(argv):
    """Starts the bokeh server and the TCP listener"""

    logger = Logger()
    opt = args_parse(sys.argv[1:])

    if opt.import_path:
        DataAggregator(import_path=opt.import_path)
    else:
        DataAggregator(auto_save=(not opt.no_save), save_path=opt.save_path)

    server = bk_server(io_loop=IOLoop().current(), port=int(opt.bokeh_port))
    server.start()

    tcp_queue = Queue()
    tcp_server = TCP_Server(queue=tcp_queue)
    tcp_server.listen(opt.listen_port)
    tcp_thread = threading.Thread(target=lambda: handle_response(tcp_queue))
    tcp_thread.daemon = True
    tcp_thread.start()

    work_queue = WorkerQueue()
    work_thread = threading.Thread(target=lambda: worker_thread(work_queue))
    work_thread.daemon = True
    work_thread.start()

    logger.info(f"Bokeh server started on http://localhost:{opt.bokeh_port}")
    server.io_loop.start()

    tcp_thread.join()
    work_thread.join()


def main():
    server(sys.argv)
