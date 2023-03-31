# coding=utf-8
# Copyright 2018-2022 EVA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
from test.util import (
    FRAME_SIZE,
    NUM_FRAMES,
    create_dummy_batches,
    create_sample_video,
    file_remove,
)

import pytest

from eva.constants import IFRAMES
from eva.expression.abstract_expression import ExpressionType
from eva.expression.comparison_expression import ComparisonExpression
from eva.expression.constant_value_expression import ConstantValueExpression
from eva.expression.logical_expression import LogicalExpression
from eva.expression.tuple_value_expression import TupleValueExpression
from eva.readers.decord_reader import DecordReader


@pytest.mark.notparallel
class DecordLoaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.video_file_url = create_sample_video()
        self.frame_size = FRAME_SIZE[0] * FRAME_SIZE[1] * 3

    @classmethod
    def tearDownClass(self):
        file_remove("dummy.avi")

    def _batches_to_reader_convertor(self, batches):
        new_batches = []
        for batch in batches:
            batch.drop_column_alias()
            new_batches.append(batch.project(["id", "data", "seconds"]))
        return new_batches

    def test_should_sample_only_iframe(self):
        for k in range(1, 10):
            video_loader = DecordReader(
                file_url=self.video_file_url,
                sampling_type=IFRAMES,
                sampling_rate=k,
            )
            batches = list(video_loader.read())

            expected = self._batches_to_reader_convertor(
                create_dummy_batches(filters=[i for i in range(0, NUM_FRAMES, k)])
            )

            self.assertEqual(batches, expected)

    def test_should_sample_every_k_frame_with_predicate(self):
        col = TupleValueExpression("id")
        val = ConstantValueExpression(NUM_FRAMES // 2)
        predicate = ComparisonExpression(
            ExpressionType.COMPARE_GEQ, left=col, right=val
        )
        for k in range(2, 4):
            video_loader = DecordReader(
                file_url=self.video_file_url,
                sampling_rate=k,
                predicate=predicate,
            )
            batches = list(video_loader.read())
            value = NUM_FRAMES // 2
            start = value + k - (value % k) if value % k else value
            expected = self._batches_to_reader_convertor(
                create_dummy_batches(filters=[i for i in range(start, NUM_FRAMES, k)])
            )
        self.assertEqual(batches, expected)

        value = 2
        predicate_1 = ComparisonExpression(
            ExpressionType.COMPARE_GEQ,
            left=TupleValueExpression("id"),
            right=ConstantValueExpression(value),
        )
        predicate_2 = ComparisonExpression(
            ExpressionType.COMPARE_LEQ,
            left=TupleValueExpression("id"),
            right=ConstantValueExpression(8),
        )
        predicate = LogicalExpression(
            ExpressionType.LOGICAL_AND, predicate_1, predicate_2
        )
        for k in range(2, 4):
            video_loader = DecordReader(
                file_url=self.video_file_url,
                sampling_rate=k,
                predicate=predicate,
            )
            batches = list(video_loader.read())
            start = value + k - (value % k) if value % k else value
            expected = self._batches_to_reader_convertor(
                create_dummy_batches(filters=[i for i in range(start, 8, k)])
            )
        self.assertEqual(batches, expected)

    def test_should_return_one_batch(self):
        video_loader = DecordReader(
            file_url=self.video_file_url,
        )
        batches = list(video_loader.read())
        expected = self._batches_to_reader_convertor(create_dummy_batches())
        self.assertEqual(batches, expected)

    def test_should_return_batches_equivalent_to_number_of_frames(self):
        video_loader = DecordReader(
            file_url=self.video_file_url,
            batch_mem_size=self.frame_size,
        )
        batches = list(video_loader.read())
        expected = self._batches_to_reader_convertor(create_dummy_batches(batch_size=1))
        self.assertEqual(batches, expected)

    def test_should_sample_every_k_frame(self):
        for k in range(1, 10):
            video_loader = DecordReader(
                file_url=self.video_file_url,
                sampling_rate=k,
            )
            batches = list(video_loader.read())
            expected = self._batches_to_reader_convertor(
                create_dummy_batches(filters=[i for i in range(0, NUM_FRAMES, k)])
            )
            self.assertEqual(batches, expected)
