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
md_version = "2.0.1"
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
    score: float


class Plugin(PluginInstance, GeneratorQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)

    def defaultTrigger(self):
        return "kill "

    def items(self, ctx):
        results = []
        uid = os.getuid()
        matcher = Matcher(ctx.query)

        for proc in psutil.process_iter(["pid", "name", "cmdline", "uids"]):

            if not ctx.isValid:
                return

            try:
                if proc.info["uids"].real != uid:
                    continue

                pid = proc.info["pid"]
                name = proc.info["name"]
                cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""

                if match := matcher.match(name, cmdline):
                    results.append(RankedItem(
                        item=StandardItem(
                            id="kill",
                            icon_factory=lambda: makeGraphemeIcon("💀"),
                            text=name,
                            subtext=cmdline,
                            actions=[
                                Action(
                                    "terminate",
                                    "Terminate",
                                    lambda pid_=pid: os.kill(pid_, SIGTERM),
                                ),
                                Action(
                                    "kill",
                                    "Kill",
                                    lambda pid_=pid: os.kill(pid_, SIGKILL),
                                )
                            ]
                        ),
                        score=match.score
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, AttributeError) as e:
                warning(f"{e.__class__.__name__}: {e}")
                continue

        yield [r.item for r in sorted(results, key=lambda x: x.score, reverse=True)]
