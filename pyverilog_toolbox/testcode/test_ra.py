#-------------------------------------------------------------------------------
# test_ra.py
#
#
#
# Copyright (C) 2015, Ryosuke Fukatani
# License: Apache 2.0
#-------------------------------------------------------------------------------


import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

from pyverilog_toolbox.verify_tool.regmap_analyzer import *
from pyverilog_toolbox.verify_tool.combloop_finder import *
from pyverilog_toolbox.verify_tool.bindlibrary import *
from pyverilog_toolbox.verify_tool.cnt_analyzer import *
from pyverilog_toolbox.verify_tool.codeclone_finder import CodeCloneFinder
from pyverilog_toolbox.verify_tool.unreferenced_finder import UnreferencedFinder
from pyverilog_toolbox.verify_tool.metrics_calculator import MetricsCalculator
import unittest

class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def test_metrics(self):
        m_calculator = MetricsCalculator("metrics_test.v")
        m_metrics, _, _ = m_calculator.synth_profile()
        self.assertEqual(m_metrics.m_ordered['TOP'], 27)
        self.assertEqual(m_metrics.m_ordered['TOP.sub'], 19)

    def test_metrics2(self):
        m_calculator = MetricsCalculator("metrics_test2.v")
        m_metrics, r_metrics, _ = m_calculator.synth_profile()
        self.assertEqual(m_metrics.m_ordered['TOP'], 19)
        self.assertEqual(r_metrics.m_ordered[('TOP', 0)], 25)

    def test_metrics_func(self):
        m_calculator = MetricsCalculator("metrics_func.v")
        m_metrics, r_metrics, f_metrics = m_calculator.synth_profile()
        self.assertEqual(m_metrics.m_ordered['TOP'], 19)
        self.assertEqual(r_metrics.m_ordered[('TOP', 0)], 1)
        self.assertEqual(f_metrics.m_ordered[('TOP.md_always0.al_block0.al_functioncall0', 0)], 9)

    def test_reg_clone(self):
        cc_finder = CodeCloneFinder("reg_clone.v")
        clones = sorted(cc_finder.search_regclone(), key = lambda t: str(t[0]))
        ordered_clones = []
        for clone in clones:
            ordered_clones.append(str(tuple(sorted(clone, key=lambda t:str(t)))))
        ordered_clones = sorted(ordered_clones, key=lambda t:str(t))
        self.assertEqual(ordered_clones,
                        ['((TOP.reg1, 0), (TOP.reg3, 0))', '((TOP.reg3, 0), (TOP.sub.reg1, 0))'])

        inv_reg_description = set([str(inv_pair) for inv_pair in cc_finder.search_invert_regs()])
        ok1 = ('((TOP.reg1, 0), (TOP.reg4, 0))' in inv_reg_description) or ('((TOP.reg4, 0), (TOP.reg1, 0))' in inv_reg_description)
        ok2 = ('((TOP.reg3, 0), (TOP.reg4, 0))' in inv_reg_description) or ('((TOP.reg4, 0), (TOP.reg3, 0))' in inv_reg_description)
        ok3 = ('((TOP.sub.reg1, 0), (TOP.reg4, 0))' in inv_reg_description) or ('((TOP.reg4, 0), (TOP.sub.reg1, 0))' in inv_reg_description)
        self.assertTrue(ok1 or ok2 or ok3)

    def test_unreferenced(self):
        u_finder = UnreferencedFinder("unreferenced_variables.v")
        self.assertEqual(str(sorted(u_finder.search_unreferenced(), key=lambda x:str(x))),
                        "['TOP.IN2', 'TOP.reg2', 'TOP.reg3', 'TOP.sub.IN']")

    def test_floating(self):
        u_finder = UnreferencedFinder("floating.v")
        self.assertEqual(str(sorted(u_finder.search_floating(), key=lambda x:str(x))),
                        "['TOP.in1', 'TOP.reg2']")

    def test_floating2(self):
        u_finder = UnreferencedFinder("floating2.v")
        self.assertEqual(str(sorted(u_finder.search_floating(), key=lambda x:str(x))),
                        "['TOP.IN', 'TOP.reg1[1]', 'TOP.reg3[2]']")

    def test_cnt_analyzer(self):
        c_analyzer = CntAnalyzer("norm_cnt2.v")
        cnt_dict = c_analyzer.analyze_cnt()
        self.assertEqual(cnt_dict['TOP.down_cnt'].tostr(),
                        "name: TOP.down_cnt\ncategory: down counter\nreset val: 0" +
                        "\nmax_val: 4\nmother counter:()")
        self.assertEqual(cnt_dict['TOP.up_cnt'].tostr(),
                        'name: TOP.up_cnt\ncategory: up counter\nreset val: 0' +
                        '\nmax_val: 5\nmother counter:()')
        self.assertEqual(cnt_dict['TOP.up_cnt2'].tostr(),
                        "name: TOP.up_cnt2\ncategory: up counter\nreset val: 0" +
                        "\nmax_val: 4\nmother counter:('TOP.up_cnt',)")
##        c_analyzer.make_cnt_event_all()
##        cnt_event_result = str(c_analyzer.cnt_dict['TOP.up_cnt'].cnt_event_dict).replace('"','')
##        print(cnt_event_result)
##        self.assertEqual(cnt_event_result,
##                        "{2: [TOP.now=TOP_now @(TOP_up_cnt==3'd2), TOP.now='d1 @(TOP_up_cnt==3'd2)], 4: [TOP.now='d0 @(TOP_up_cnt==3'd4)]}")

    def test_cnt_analyzer2(self):
        c_analyzer = CntAnalyzer("norm_cnt.v")
        cnt_dict = c_analyzer.analyze_cnt()
        self.assertEqual(cnt_dict['TOP.up_cnt'].tostr(),
                        "name: TOP.up_cnt\ncategory: up counter\nreset val: 0" +
                        "\nmax_val: 7\nmother counter:()")

    def test_normal(self):
        ranalyzer = RegMapAnalyzer("regmap.v", "setup.txt")
        write_map, read_map = ranalyzer.getRegMaps()
        self.assertEqual(str(write_map.map), "{0: {0: ('TOP.reg0', 0), 1: ('TOP.reg0', 1)}, 1: {0: ('TOP.reg1', 0)}}")
        self.assertEqual(str(read_map.map), "{0: {0: ('TOP.reg0', 0), 1: ('TOP.reg0', 1)}, 1: {0: ('TOP.reg1', 0)}}")

    def test_split(self):
        ranalyzer = RegMapAnalyzer("regmap_split.v", "setup.txt")
        write_map, read_map = ranalyzer.getRegMaps()
        self.assertEqual(str(write_map.map),
                        "{1: {0: ('TOP.reg0', 0), 1: ('TOP.reg0', 1), 2: ('TOP.reg1', 0), 3: ('TOP.reg1', 1)}}")
        self.assertEqual(str(read_map.map),
                        "{1: {0: ('TOP.reg0', 0), 1: ('TOP.reg0', 1), 2: ('TOP.reg1', 0), 3: ('TOP.reg1', 1)}}")

    def test_partselect(self):
        df = dataflow_facade("complex_partselect.v")
        term_dict = df.make_extract_dfterm_dict()
        self.assertEqual(term_dict[('TOP.reg0', 3)], set(['(TOP.WRITE_DATA, 1)', '(TOP.WRITE, 0)', '(TOP.reg0, 3)']))
        self.assertEqual(term_dict[('TOP.reg0', 4)], set(['(TOP.WRITE_DATA, 2)', '(TOP.WRITE, 0)', '(TOP.reg0, 4)']))

    def test_split2(self):
        ranalyzer = RegMapAnalyzer("regmap2.v", "setup.txt")
        write_map, read_map = ranalyzer.getRegMaps()
        self.assertEqual(str(write_map.map),
                        "{0: {0: ('TOP.reg0', 3), 1: ('TOP.reg0', 4)}}")
        self.assertEqual(str(read_map.map),
                        "{0: {0: ('TOP.reg0', 3), 1: ('TOP.reg0', 4)}}")

    def test_comb_loop(self):
        c_finder = CombLoopFinder("combloop.v")
        with self.assertRaises(CombLoopException):
            c_finder.search_combloop()
        c_finder = CombLoopFinder("not_combloop.v")
        c_finder.search_combloop()

    def test_comb_loop1(self):
        c_finder = CombLoopFinder("combloop1.v")
        with self.assertRaises(CombLoopException):
            c_finder.search_combloop()

    def test_comb_loop2(self):
        c_finder = CombLoopFinder("combloop2.v")
        with self.assertRaises(CombLoopException):
            c_finder.search_combloop()

    def test_comb_loop4(self):
        c_finder = CombLoopFinder("combloop4.v")
        with self.assertRaises(CombLoopException):
            c_finder.search_combloop()

if __name__ == '__main__':
    unittest.main()
