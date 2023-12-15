import core.process as module
from tests import Materials


def test_process_node():
    inputs = Materials(a=2, b=4)
    outputs = Materials(c=2, d=4)

    module.ProcessNode("Test", inputs, outputs, 0, 0)


def test_process_node_shift():
    inputs = Materials(a=2, b=4)
    midputs = Materials(e=4, f=7)
    outputs = Materials(c=2, d=4)

    first = module.ProcessNode("first", inputs, midputs, 0, 0)
    second = module.ProcessNode("second", midputs, outputs, 0, 0)

    assert inputs >> first == midputs
    assert inputs >> first >> second == outputs
    assert 2*inputs >> first >> second == 2*outputs

    assert second >> outputs == midputs
    assert first >> second >> outputs == inputs
    assert first >> second >> 2*outputs == 2*inputs
    

