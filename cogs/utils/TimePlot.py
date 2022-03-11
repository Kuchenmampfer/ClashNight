from datetime import timedelta, datetime
from typing import Union

import discord
import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pytz

from cogs.utils.functions import plot2embed

matplotlib.use('Agg')


class TimePlot:
    def __init__(self, title: str, offset_days: Union[int, float], event_data: bool,
                 y_label: str, timezone=pytz.timezone('Europe/Berlin')):
        self.title: str = title
        self.y_label = y_label
        self.event_data = event_data
        self.data = {}
        self.chosen_account = 'all accounts'
        self.offset = timedelta(offset_days)
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.timezone = timezone
        self.current_end_time = datetime.now(self.timezone)

    def add_data(self, tag: str, name: str, times: list, data: list):
        if self.event_data:
            times_ext = []
            for i in range(len(times) - 1):
                times_ext.append(times[i])
                times_ext.append(times[i + 1] - timedelta(seconds=30))
            times_ext.append(times[-1])
            data_ext = []
            for item in data:
                for i in range(2):
                    data_ext.append(item)
            times_ext = np.array(times_ext)
            data_ext = np.array(data_ext)
            self.data[tag] = (name, times_ext, data_ext[:-1])
        else:
            times = np.array(times)
            data = np.array(data)
            self.data[tag] = (name, times, data)

    def next(self):
        self.current_end_time = min(self.current_end_time + self.offset, datetime.now(self.timezone))

    def previous(self):
        self.current_end_time = max(self.current_end_time - self.offset,
                                    min([data[0][0] for data in self.data.values()]) + self.offset)

    def now(self):
        self.current_end_time = datetime.now(self.timezone)

    def plot(self) -> discord.File:
        self.ax.clear()
        for tag, (name, times, data) in self.data.items():
            if self.chosen_account in ['all accounts', tag]:
                times = np.array([time.astimezone(self.timezone) for time in times])
                mask = (self.current_end_time - self.offset < times) & (times < self.current_end_time)
                self.ax.plot_date(times[mask], data[mask], '-', label=name)

        loc = matplotlib.dates.AutoDateLocator()
        formatter = matplotlib.dates.ConciseDateFormatter(loc)
        self.ax.xaxis.set_major_locator(loc)
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.xaxis.set_tick_params(which="major", labelsize=12)
        self.ax.set_title(self.title)
        self.ax.set_ylabel(self.y_label)
        self.ax.set_xlabel('Date/Time')
        self.ax.legend()
        self.ax.axes.grid()
        self.ax.autoscale(True, 'x', True)
        image: discord.file = plot2embed(self.ax)
        return image
