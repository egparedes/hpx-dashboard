# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""
"""

import os

from bokeh.layouts import row, column
from bokeh.models import Panel, Tabs
from bokeh.themes import Theme

from jinja2 import Environment, FileSystemLoader

from .utils import Notifier
from .data import format_instance
from .plots import TasksPlot, TimeSeries
from .widgets import DataCollectionWidget, CustomCounterWidget
from ..common.constants import task_cmap

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "http", "templates"))
)
BOKEH_THEME = Theme(os.path.join(os.path.dirname(__file__), "http", "bokeh_theme.yaml"))


def custom_counters_widget(doc, notifier):
    """Defines the tab for the custom counter widget"""
    custom_counter = CustomCounterWidget(doc)
    return custom_counter.layout()


def scheduler_widget(doc, notifier):
    """Defines the tab for the scheduler plot"""

    # TODO : if there are multiple pools, plot all the lines

    scheduler_plot = TimeSeries(
        doc, shade=False, title="Scheduler utilization", y_axis_label="Utilization (%)"
    )
    counter = "scheduler/utilization/instantaneous"
    instance = format_instance("0")
    pretty_name = "Scheduler utilization"
    scheduler_plot.add_line(
        counter,
        instance,
        pretty_name=pretty_name,
    )

    def _reset_lines(collection):
        nonlocal scheduler_plot

        scheduler_plot.remove_all()
        scheduler_plot.add_line(counter, instance, collection, pretty_name=pretty_name)

    notifier.subscribe(_reset_lines)
    return scheduler_plot.layout()


def tasks_widget(doc, notifier, cmap):
    """Defines the tab for the task plot"""
    task_plot = TasksPlot(doc, cmap=cmap)
    notifier.subscribe(task_plot.set_collection)
    return task_plot.layout()


def standalone_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    widget = DataCollectionWidget(doc, notifier.notify)

    cmap = task_cmap
    if "cmap" in extra:
        cmap = extra["cmap"]

    task_tab = Panel(
        child=tasks_widget(doc, notifier, cmap),
        title="Tasks plot",
    )
    scheduler_tab = Panel(child=scheduler_widget(doc, notifier), title="Scheduler utilization")
    custom_counter_tab = Panel(
        child=custom_counters_widget(doc, notifier), title="Customizable plots"
    )

    doc.add_root(
        row(
            Tabs(tabs=[scheduler_tab, task_tab, custom_counter_tab]),
            widget.layout(),
            sizing_mode="scale_width",
        )
    )

    doc.template = env.get_template("normal.html")
    doc.template_variables.update(extra)
    doc.theme = BOKEH_THEME


def tasks_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    widget = DataCollectionWidget(doc, notifier.notify)
    cmap = task_cmap
    if "cmap" in extra:
        cmap = extra["cmap"]
    tasks = tasks_widget(doc, notifier, cmap)

    doc.add_root(column(widget.layout(), tasks))


def scheduler_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    widget = DataCollectionWidget(doc, notifier.notify)
    scheduler = scheduler_widget(doc, notifier)

    doc.add_root(column(widget.layout(), scheduler))


def custom_counter_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    custom = custom_counters_widget(doc, notifier)

    doc.add_root(custom)
