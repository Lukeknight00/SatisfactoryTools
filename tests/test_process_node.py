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


def test_simple_optimization_minimize_input():
    inputs = Materials(a=2, b=4)
    midputs = Materials(e=4, f=7)
    outputs = Materials(c=2, d=4)

    source = module.ProcessNode("source", Materials(), inputs, 0, 0)
    first = module.ProcessNode("first", inputs, midputs, 0, 0)
    second = module.ProcessNode("second", midputs, outputs, 0, 0)

    optimal = module.Process.minimize_input(4*outputs, [source, first, second], include_power=False)

    # result should have 4*first
    breakpoint()


def test_optimization_extraneous_recipes_minimize_input():
    inputs = Materials(a=2, b=4)
    midputs = Materials(e=4, f=7)
    outputs = Materials(c=2, d=4)

    extraneous = Materials(g=1, h=9)

    source = module.ProcessNode("source", Materials(), inputs, 0, 0)
    first = module.ProcessNode("first", inputs, midputs, 0, 0)
    second = module.ProcessNode("second", midputs, outputs, 0, 0)
    third = module.ProcessNode("third", inputs, extraneous, 0, 0)
    fourth = module.ProcessNode("fourth", extraneous, midputs, 0, 0)

    optimal = module.Process.minimize_input(4*outputs, [source, first, second, third, fourth], include_power=False)

    # result should have 4*first
    breakpoint()
#
# def test_optimization_loop_available_minimize_input():
#     pass
#
# def test_optimization_simple_maximize_output():
#     pass
#
# def test_optimization_extraneous_recipes_maximize_output():
#     pass
#
# def test_optimization_loop_available_maximize_output():
#     pass


# TODO: tests that include power
# TODO: tests with fork in solution
