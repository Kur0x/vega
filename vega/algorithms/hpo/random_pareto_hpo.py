# -*- coding:utf-8 -*-

# Copyright (C) 2020. Huawei Technologies Co., Ltd. All rights reserved.
# This program is free software; you can redistribute it and/or modify
# it under the terms of the MIT License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# MIT License for more details.

"""Defined RandomParetoHpo class."""
import os
import logging
import copy
from vega.algorithms.hpo.common import RandomPareto
from vega.core.hyperparameter_space import json_to_hps
from vega.core.common.class_factory import ClassFactory, ClassType
from vega.core.pipeline.hpo_generator import HpoGenerator


@ClassFactory.register(ClassType.HPO)
class RandomParetoHpo(HpoGenerator):
    """An Hpo of RandomPareto, inherit from HpoGenerator."""

    def __init__(self):
        """Init RandomParetoHpo."""
        super(RandomParetoHpo, self).__init__()
        hps = json_to_hps(self.cfg.hyperparameter_space)
        self.hpo = RandomPareto(hps,
                                self.policy.config_count,
                                self.policy.total_epochs,
                                object_count=int(self.policy.pareto.object_count),
                                max_object_ids=self.policy.pareto.max_object_ids
                                )

    def sample(self):
        """Sample an id and hps from hpo.

        :return: id, hps
        :rtype: int, dict
        """
        sample = self.hpo.propose()
        if sample is not None:
            sample = copy.deepcopy(sample)
            sample_id = sample.get('config_id')
            self._hps_cache[str(sample_id)] = [copy.deepcopy(sample), []]
            re_hps = sample.get('configs')
            if 'epoch' in sample:
                re_hps['trainer.epochs'] = sample.get('epoch')
            return sample_id, re_hps
        else:
            return None, None

    def update_performance(self, hps, performance):
        """Update current performance into hpo score board.

        :param hps: hyper parameters need to update
        :param performance:  trainer performance

        """
        if isinstance(performance, list) and len(performance) > 0:
            self.hpo.add_score(int(hps.get('config_id')), performance)
        else:
            # TODO: multi object will be set None later
            logging.error("hpo get empty performance!")

    @property
    def is_completed(self):
        """Make hpo pipe step status is completed.

        :return: hpo status
        :rtype: bool

        """
        return self.hpo.is_completed

    @property
    def best_hps(self):
        """Get best hps.

        In radnom_pareto, there exits multiple models that don't dominate each other.
        For demo, just pick the first one of the list.
        self.hpo.best_config() is a list of dict, remove [0] for custimized design.
        """
        return self.hpo.best_config()[0]

    def _save_score_board(self):
        """Save the internal score board for detail analysis."""
        try:
            self.hpo.sieve_board.to_csv(self._board_file, index=None, header=True)
        except Exception as e:
            logging.error("Failed to save score board file, error={}".format(str(e)))
