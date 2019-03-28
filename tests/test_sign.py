# -*- coding: utf-8 -*-
import unittest

from discovery.util import signature


class TestSign(unittest.TestCase):
    def test_sign(self):
        secret = "3cf6bd1b0ff671021da5f424fea4b04a"
        data = {"Hello": "world", "test1": "test"}
        sign1 = "18f1be881a5937c097dab04621707da9"
        sign2 = "7f86dedfff3fc902de364c4522af8de1"
        self.assertEqual(signature(data, secret, True), sign1)
        self.assertEqual(signature(data, secret), sign2)
