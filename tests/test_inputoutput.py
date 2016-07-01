import unittest
import random
import io
import pyrtl
from pyrtl import inputoutput


full_adder_blif = """\
# Generated by Yosys 0.3.0+ (git sha1 7e758d5, clang 3.4-1ubuntu3 -fPIC -Os)
.model full_adder
.inputs x y cin
.outputs sum cout
.names $false
.names $true
1
.names y $not$FA.v:12$3_Y
0 1
.names x $not$FA.v:11$1_Y
0 1
.names cin $not$FA.v:15$6_Y
0 1
.names ind3 ind4 sum
1- 1
-1 1
.names $not$FA.v:15$6_Y ind2 ind3
11 1
.names x $not$FA.v:12$3_Y ind1
11 1
.names ind2 $not$FA.v:16$8_Y
0 1
.names cin $not$FA.v:16$8_Y ind4
11 1
.names x y $and$FA.v:19$11_Y
11 1
.names ind0 ind1 ind2
1- 1
-1 1
.names cin ind2 $and$FA.v:19$12_Y
11 1
.names $and$FA.v:19$11_Y $and$FA.v:19$12_Y cout
1- 1
-1 1
.names $not$FA.v:11$1_Y y ind0
11 1
.end
"""

state_machine_blif = """\
# Generated by Yosys 0.5+     420 (git sha1 1d62f87, clang 7.0.2 -fPIC -Os)

.model statem
.inputs clk in reset
.outputs out[0] out[1] out[2] out[3]
.names $false
.names $true
1
.names $undef
.names in state[2] $abc$129$n11_1
11 1
.names $abc$129$n11_1 state[3] $auto$fsm_map.cc:238:map_fsm$30[0]
1- 1
-1 1
.names state[2] $abc$129$n13
0 1
.names state[0] $abc$129$n14_1
0 1
.names state[2] state[1] $abc$129$n15
00 1
.names $abc$129$n15 $abc$129$n14_1 $abc$129$n13 out[0]
-00 1
0-0 1
.names state[1] $abc$129$n17
0 1
.names $abc$129$n15 $abc$129$n14_1 $abc$129$n17 out[1]
-00 1
0-0 1
.names $abc$129$n15 $abc$129$n14_1 out[2]
11 1
.names in $abc$129$n13 $auto$fsm_map.cc:118:implement_pattern_cache$38
00 1
# .subckt $_DFF_PP1_ C=clk D=$auto$fsm_map.cc:238:map_fsm$30[0] Q=state[0] R=reset
# .subckt $_DFF_PP0_ C=clk D=$auto$fsm_map.cc:118:implement_pattern_cache$38 Q=state[1] R=reset
# .subckt $_DFF_PP0_ C=clk D=state[0] Q=state[2] R=reset
# .subckt $_DFF_PP0_ C=clk D=state[1] Q=state[3] R=reset
.names $false out[3]
1 1
.end
"""

class TestInputFromBlif(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_combo_blif_input_no_crashy(self):
        pyrtl.input_from_blif(full_adder_blif)
        x, y, cin = [pyrtl.working_block().get_wirevector_by_name(s) for s in ['x', 'y', 'cin']]
        io_vectors = pyrtl.working_block().wirevector_subset((pyrtl.Input, pyrtl.Output))

    def test_sequential_blif_input_no_crashy(self):
        pyrtl.input_from_blif(state_machine_blif)
        io = pyrtl.working_block().wirevector_subset((pyrtl.Input, pyrtl.Output))


class TestOutputGraphs(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_output_to_tgf_does_not_throw_error(self):
        with io.StringIO() as vfile:
            pyrtl.input_from_blif(full_adder_blif)
            pyrtl.output_to_trivialgraph(vfile)

    def test_output_to_graphviz_does_not_throw_error(self):
        with io.StringIO() as vfile:
            pyrtl.input_from_blif(full_adder_blif)
            pyrtl.output_to_graphviz(vfile)


class TestOutputTextbench(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_verilog_testbench_does_not_throw_error(self):
        zero = pyrtl.Input(1, 'zero')
        counter_output = pyrtl.Output(3, 'counter_output')
        counter = pyrtl.Register(3, 'counter')
        counter.next <<= pyrtl.mux(zero, counter + 1, 0)
        counter_output <<= counter
        sim_trace = pyrtl.SimulationTrace([counter_output, zero])
        sim = pyrtl.Simulation(tracer=sim_trace)
        for cycle in range(15):
            sim.step({zero: random.choice([0, 0, 0, 1])})
        with io.StringIO() as tbfile:
            pyrtl.OutputVerilogTestbench(tbfile, sim_trace)


class TestNetGraph(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_as_graph(self):
        inwire = pyrtl.Input(bitwidth=1, name="inwire1")
        inwire2 = pyrtl.Input(bitwidth=1)
        inwire3 = pyrtl.Input(bitwidth=1)
        tempwire = pyrtl.WireVector()
        tempwire2 = pyrtl.WireVector()
        outwire = pyrtl.Output()

        tempwire <<= inwire | inwire2
        tempwire2 <<= ~tempwire
        outwire <<= tempwire2 & inwire3

        g = inputoutput.net_graph()
        # note for future: this might fail if we change
        # the way that temp wires are inserted, but that
        # should not matter for this test and so the number
        # can be safely updated.
        self.assertEqual(len(g), 10)


class TestVerilogNames(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()
        self.vnames = inputoutput._VerilogSanitizer("_sani_test")

    def checkname(self, name):
        self.assertEqual(self.vnames.make_valid_string(name), name)

    def assert_invalid_name(self, name):
        self.assertNotEqual(self.vnames.make_valid_string(name), name)

    def test_verilog_check_valid_name_good(self):
        self.checkname('abc')
        self.checkname('a')
        self.checkname('BC')
        self.checkname('Kabc')
        self.checkname('B_ac')
        self.checkname('_asdvqa')
        self.checkname('_Bs_')
        self.checkname('fd$oeoe')
        self.checkname('_B$$s')
        self.checkname('B')

    def test_verilog_check_valid_name_bad(self):
        self.assert_invalid_name('carne asda')
        self.assert_invalid_name('')
        self.assert_invalid_name('asd%kask')
        self.assert_invalid_name("flipin'")
        self.assert_invalid_name(' jklol')
        self.assert_invalid_name('a' * 2000)


class TestVerilog(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_romblock_does_not_throw_error(self):
        from pyrtl.corecircuits import _basic_add
        a = pyrtl.Input(bitwidth=3, name='a')
        b = pyrtl.Input(bitwidth=3, name='b')
        o = pyrtl.Output(bitwidth=3, name='o')
        res = _basic_add(a,b)
        rdat = {0: 1, 1: 2, 2: 5, 5: 0}
        mixtable = pyrtl.RomBlock(addrwidth=3, bitwidth=3, romdata=rdat)
        o <<= mixtable[res[:-1]]
        with io.StringIO() as testbuffer:
            pyrtl.OutputToVerilog(testbuffer)

    def test_textual_correctness(self):
        pass


if __name__ == "__main__":
    unittest.main()
