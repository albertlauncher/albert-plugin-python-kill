# -*- coding: utf-8 -*-
# Copyright (c) 2022 Manuel Schneider
# Copyright (c) 2022 Benedict Dudel
# Copyright (c) 2022 Pete Hamlin
import dataclasses
import os
from signal import SIGKILL, SIGTERM

from albert import *
import psutil

md_iid = "5.0"
md_version = "2.1.0"
md_name = "Kill Process"
md_description = "Kill processes"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-kill"
md_authors = ["@Pete-Hamlin", "@BenedictDudel", "@ManuelSchneid3r"]
md_maintainers = ["@Pete-Hamlin", "@ManuelSchneid3r"]
md_lib_dependencies = ["psutil"]

@dataclasses.dataclass
class RankedItem:
    item: StandardItem
    match: Match


class Plugin(PluginInstance, GeneratorQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)
        self.fuzzy = False

    def supportsFuzzyMatching(self):
        return True

    def setFuzzyMatching(self, enabled):
        self.fuzzy = enabled

    def defaultTrigger(self):
        return "kill "

    @dataclasses.dataclass
    class Process:
        pid: int
        name: str
        cmdline: str

    @staticmethod
    def _get_user_processes(uid):
        for proc in psutil.process_iter(["pid", "name", "cmdline", "uids"]):
            try:
                if proc.info["uids"].real != uid:
                    continue

                yield Plugin.Process(
                    pid=proc.info["pid"],
                    name=proc.info["name"],
                    cmdline=" ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, AttributeError) as e:
                warning(f"{e.__class__.__name__}: {e}")
                continue

    @staticmethod
    def _make_item(proc: Process):
        return StandardItem(
            id="kill",
            icon_factory=lambda: Icon.grapheme("💀"),
            text=proc.name,
            subtext=proc.cmdline,
            actions=[
                Action(
                    "terminate",
                    "Terminate",
                    lambda pid_=proc.pid: os.kill(pid_, SIGTERM),
                ),
                Action(
                    "kill",
                    "Kill",
                    lambda pid_=proc.pid: os.kill(pid_, SIGKILL),
                )
            ]
        )

    def items(self, ctx):
        matcher = Matcher(ctx.query, MatchConfig(fuzzy=self.fuzzy))

        rank_items = [
            RankedItem(self._make_item(proc), matcher.match(proc.name, proc.cmdline))
            for proc in self._get_user_processes(os.getuid())
        ]

        yield [
            r.item for r in sorted(rank_items, key=lambda x: x.match.score, reverse=True)
            if r.match.isMatch()
        ]
